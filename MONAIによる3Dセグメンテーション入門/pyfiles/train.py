from tqdm import tqdm
from monai.losses import DiceCELoss
from monai.metrics import DiceMetric
from torch import optim
import os
from monai.transforms import AsDiscrete
from monai.data import decollate_batch
from monai.inferers import sliding_window_inference
import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter




class EarlyStopping:
    def __init__(self, patience=1, verbose=False, delta=0):
        self.best_score = None
        self.current_score = None
        self.counter = 0
        self.patiece = patience
        self.delta = delta
        self.earlystop = False
        self.verbose = verbose
    def __call__(self, val_metric):
        self.current_score = val_metric

        if self.best_score == None:
            self.best_score = val_metric

        elif self.current_score - self.best_score > self.delta:
            self.best_score = self.current_score
            self.counter += 1
            if self.counter == self.patiece:
                self.earlystop = True
        

    def Print_score(self):
        if self.verbose == True:
            print(f"Val loss(Current):{self.current_score}")
            
    def set_false(self):
        self.earlystop = False
        self.counter = 0



class TrainLoop:
    def __init__(self,model,config,train_dataloader,val_dataloader,device,run_name=""):
        self.model = model
        self.n_epochs = config["max_epochs"]
        self.lr = config["lr"]
        self.loss = DiceCELoss(to_onehot_y=True, softmax=True)
        self.optimizer = optim.AdamW(model.parameters(), lr=self.lr, weight_decay=1e-5)
        self.dice_metric = DiceMetric(include_background=False, reduction="mean_batch", get_not_nans=False)
        self.scaler = torch.cuda.amp.GradScaler()
        self.train_loader = train_dataloader
        self.val_loader = val_dataloader
        self.device = device
        self.out_channels = config["class_num"]
        self.label_names = config["label_names"].keys()
        self.post_label = AsDiscrete(to_onehot=config["class_num"]) # class n
        self.post_pred = AsDiscrete(argmax=True, to_onehot=config["class_num"]) # class n
        self.sw_batch_num = config["sw_batch_size"]
        self.rand_crop_size = config["model_params"]["image_size"]
        self.val_interval = config["val_interval"]
        self.run_name = run_name
        self.infer_device = (config["infer_device"] if config["infer_device"] == "cpu" else self.device)
        self.early_stopping = EarlyStopping()
        self.writer = SummaryWriter(log_dir="/kqi/output/logs")
        
        
    
    def train(self,over_write=True):
        
        os.makedirs(f"/kqi/output/net_params/{self.run_name}",exist_ok=over_write)

        
        for epoch in tqdm(range(1,self.n_epochs+1)):
            if epoch % self.val_interval == 0:
                train_mean_epoch_loss = self.train_epoch()
                val_mean_epoch_loss, val_dice_metrics = self.validate_epoch()

                print(f"【Epoch:{epoch}】\n Train loss:{train_mean_epoch_loss:.7f} \
                  \n Val loss:{val_mean_epoch_loss:.7f} Val dice score:{np.mean(val_dice_metrics):.7f}")


                self.writer.add_scalar("train/epoch loss",train_mean_epoch_loss,epoch)
                self.writer.add_scalar("val/epoch loss",val_mean_epoch_loss,epoch)
                self.writer.add_scalar("val/mean dice score",np.mean(val_dice_metrics),epoch)

                for label_name, val_dice in zip(self.label_names,val_dice_metrics):
                    self.writer.add_scalar(f"val/{label_name} dice score",val_dice,epoch)
            



                self.early_stopping(np.mean(val_dice_metrics))
                if self.early_stopping.earlystop == True:
                    print("--Model was saved!--")
                    torch.save(self.model.state_dict(),f"/kqi/output/net_params/{self.run_name}/SwinUNETR_{self.run_name}_bestmodel.pth")
                    self.early_stopping.set_false()
            else:
                train_mean_epoch_loss = self.train_epoch()
                print(f"【Epoch:{epoch}】\n Train loss:{train_mean_epoch_loss:.7f}")

        torch.save(self.model.state_dict(),f"/kqi/output/net_params/{self.run_name}/SwinUNETR_epoch{self.n_epochs}_{self.run_name}.pth")
        self.writer.close()
        
            
    
    def train_epoch(self):
        self.model.train()
        epoch_loss = 0
        print("train loop")

        for idx, batch in enumerate(self.train_loader):
            
            images = batch["image"].to(self.device)
            labels = batch["label"].to(self.device)
            
            with torch.cuda.amp.autocast():
                logit = self.model(images)
                loss = self.loss(logit, labels)
            
            epoch_loss += loss.item()

            self.optimizer.zero_grad()
            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            self.scaler.step(self.optimizer)
            self.scaler.update()
        
            del images, labels, logit
            torch.cuda.empty_cache()
        
        mean_epoch_loss = epoch_loss / len(self.train_loader)

        return mean_epoch_loss
   
    def validate_epoch(self):
        self.model.eval()
        epoch_loss = 0
        print("validation loop")
        
        with torch.no_grad():
            for idx, batch in enumerate(self.val_loader):
            
                images = batch["image"].to(self.device)
                labels = batch["label"]
                
                with torch.cuda.amp.autocast():
                    logit = sliding_window_inference(images, self.rand_crop_size, self.sw_batch_num, self.model, device=self.infer_device)
                    logit = logit.cpu()
                    loss = self.loss(logit, labels)
                
                epoch_loss += loss.item()
                output_convert, labels_convert = self.convert_onehot(logit,labels)
                self.dice_metric(y_pred=output_convert, y=labels_convert)
                
                if torch.isnan(logit).any() or torch.isinf(logit).any():
                    print(f"NaN or Inf found in logits for batch {idx}")
                if torch.isnan(loss).any() or torch.isinf(loss).any():
                    print(f"NaN or Inf found in loss for batch {idx}")
                
            
                del images, labels, logit,output_convert, labels_convert
                torch.cuda.empty_cache()
                
            mean_epoch_loss = epoch_loss / len(self.val_loader)
            dice_metric = self.dice_metric.aggregate().tolist()
            self.dice_metric.reset()
            

        return mean_epoch_loss, dice_metric
    
    def convert_onehot(self, outputs, true_labels):
        labels_list = decollate_batch(true_labels)
        labels_convert = [self.post_label(label_tensor) for label_tensor in labels_list]
        outputs_list = decollate_batch(outputs)
        output_convert = [self.post_pred(pred_tensor) for pred_tensor in outputs_list]
        return output_convert, labels_convert
