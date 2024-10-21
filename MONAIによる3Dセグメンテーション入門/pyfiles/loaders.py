from monai.transforms import (
    EnsureChannelFirstd,
    Compose,
    Orientationd,
    LoadImaged,
    RandFlipd,
    RandCropByPosNegLabeld,
    RandShiftIntensityd,
    ScaleIntensityRanged,
    RandRotate90d,
    CenterSpatialCropd,
    SpatialPadd,
    Spacingd
)

import torch
from monai.data import DataLoader,load_decathlon_datalist, Dataset




def make_loaders(voxel_size=(1.5,1.5,1.5),image_size=(128,256, 256), patch_size=(96,96,96), samples=2, 
                 num_workers=4,dataset_path= './data_list_pyfile.json',seed=42):
    train_transforms = Compose([
                                LoadImaged(keys=["image", "label"]),
                                EnsureChannelFirstd(keys=["image", "label"]), #<class 'monai.data.meta_tensor.MetaTensor'>
                                ScaleIntensityRanged(keys=["image"],a_min=-175,a_max=250,b_min=0.0,b_max=1.0,clip=True),
                                Spacingd(keys=["image", "label"],pixdim=voxel_size,mode=("trilinear", "nearest")),
                                SpatialPadd(keys=["image", "label"], spatial_size=image_size),
                                CenterSpatialCropd(keys=["image", "label"], roi_size=image_size),
                                Orientationd(keys=["image", "label"], axcodes="RAS"),
                                RandCropByPosNegLabeld(
                                    keys=["image", "label"],
                                    label_key="label",
                                    spatial_size=patch_size,
                                    pos=1,
                                    neg=1,
                                    num_samples=samples,
                                    image_key="image",
                                    image_threshold=0,
                                ),
                                RandFlipd(
                                    keys=["image", "label"],
                                    spatial_axis=[0],
                                    prob=0.10,
                                ),
                                RandFlipd(
                                    keys=["image", "label"],
                                    spatial_axis=[1],
                                    prob=0.10,
                                ),
                                RandFlipd(
                                    keys=["image", "label"],
                                    spatial_axis=[2],
                                    prob=0.10,
                                ),
                                RandRotate90d(
                                    keys=["image", "label"],
                                    prob=0.10,
                                    max_k=3,
                                ),
                                RandShiftIntensityd(
                                    keys=["image"],
                                    offsets=0.10,
                                    prob=0.50,
                                ),
                            ]
                            )
                #output:torch.Size([2, 1, 96, 96, 96])
        
    val_transforms = Compose(
                    [
                        LoadImaged(keys=["image", "label"]),
                        EnsureChannelFirstd(keys=["image", "label"]),
                        ScaleIntensityRanged(
                            keys=["image"], a_min=-175, a_max=250, b_min=0.0, b_max=1.0, clip=True
                        ),
                        Spacingd(keys=["image", "label"],pixdim=voxel_size,mode=("trilinear", "nearest")),
                        SpatialPadd(keys=["image", "label"], spatial_size=image_size),
                        CenterSpatialCropd(keys=["image", "label"], roi_size=image_size),
                        Orientationd(keys=["image", "label"], axcodes="RAS"),
                    ]
                )

    torch.manual_seed(seed)
    train_files = load_decathlon_datalist(dataset_path, True, "training")
    val_files = load_decathlon_datalist(dataset_path, True, "testing")

    train_ds = Dataset(data=train_files, transform=train_transforms)
    val_ds = Dataset(data=val_files, transform=val_transforms)
    train_loader = DataLoader(train_ds, num_workers=num_workers, batch_size=1, shuffle=True)
    val_loader = DataLoader(val_ds, num_workers=num_workers, batch_size=1)
    
    return train_ds, val_ds, train_loader, val_loader