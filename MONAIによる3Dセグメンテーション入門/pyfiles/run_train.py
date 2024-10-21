import torch
from loaders import make_loaders
from train import TrainLoop
from monai.networks.nets import SwinUNETR
import argparse
import random
import numpy as np


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed) 
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="PyTorch Training")
    parser.add_argument("--seed", default=42, type=int, help="seed")
    parser.add_argument("--epochs", default=100, type=int, help="number of training epochs")
    parser.add_argument("--num_sumples", default=2, type=int, help="number of random crop")
    parser.add_argument("--sw_batch_size", default=2, type=int, help="number of sliding window batch size")
    parser.add_argument("--voxel_size", default=(1.5,1.5,1.5), type=tuple, help="voxel size")
    parser.add_argument("--image_size", default=(128,256,256), type=tuple, help="image size")
    parser.add_argument("--run_name", default="Swin-UNETR", type=str, help="run name")
    parser.add_argument("--infer_device", default="cpu", type=str, help="device for sliding window inference")
    parser.add_argument("--num_workers", default=4, type=int, help="number of workers")
    parser.add_argument("--dataset_jsonpath", default="./data_list_pyfile.json", type=str, help="dataset json path")
    parser.add_argument("--val_interval", default=2, type=int, help="validation interval")
    parser.add_argument("--parallel", action='store_true', help="multi gpu processing or not")
    parser.add_argument("--pretrain", action='store_true', help="use pretrained model")
    parser.add_argument("--cache_rate", default=0, type=float, help="cache rate for train dataset")
    args = parser.parse_args()


    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    RAND_CROP_SIZE = (96,96,96)  
    set_seed(args.seed)
    
    train_ds, val_ds, train_loader, val_loader = make_loaders(args.voxel_size,args.image_size,RAND_CROP_SIZE,args.num_sumples,args.cache_rate,
                                                              args.num_workers,dataset_path=args.dataset_jsonpath,seed=args.seed)
    
    
    MODEL = SwinUNETR(
                img_size=RAND_CROP_SIZE,
                in_channels=1,
                out_channels=3,
                feature_size=48,
                use_checkpoint=True,
                )
    MODEL = MODEL.to(DEVICE)
    
    if args.pretrain:
        
        print("using pretrained model")
        weight = torch.load("/kqi/input/model_swinvit.pt")
        MODEL.load_from(weights=weight)

    if args.parallel:
        MODEL = torch.nn.DataParallel(MODEL)
        
    LABEL_NAMES = {
                   "kidney": 1,
                   "tumor": 2}
    
    config = {
                "seed":args.seed,
                "num_workers": args.num_workers,
                "label_names":LABEL_NAMES,

                # train settings
                "train_batch_size": 1,
                "val_batch_size": 1,
                "lr": 1e-4,
                "max_epochs": args.epochs,
                "rand_crop_num":args.num_sumples,
                "image_size":args.image_size,
                "voxel_size":args.voxel_size,
                "val_interval":args.val_interval,
                "sw_batch_size":args.sw_batch_size,
                "infer_device":args.infer_device,


                "model_type": "Swin-UNETR", # just to keep track
                "model_params": dict(
                    image_size=RAND_CROP_SIZE,
                    feature_size=48),
                "class_num":3,
            }
    
    Trainer = TrainLoop(MODEL,config,train_loader,val_loader,DEVICE,run_name=args.run_name)
    Trainer.train()