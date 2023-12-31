#importing libraries

import os
import numpy as np
import torch
import time
import torch.utils.data
from torch.utils.data.dataset import Dataset
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import random
import cv2
import glob
from PIL import Image
import ntpath
import os
from tqdm import tqdm
from tqdm import trange

from dataset import ImageWoof
from parser import parse_arguments
from matplotlib import pyplot as plt

from torchvision.transforms import v2
from torch.utils.data import default_collate


from torchinfo import summary
from pathlib import Path

import importlib

params = parse_arguments()

print(params)

lr=params.lr
epochs=params.epochs
optimizer=params.opt
batch_size=params.batch_size
device = 'cuda'
activation=nn.ReLU()

module_name=params.model_name
path=params.output_folder + "_e" + str(params.epochs) + "_l" + str(params.lr) + "_" + str(params.opt) + "_" + str(module_name) + "_" + str(activation).split("(")[0]

best_loss = 4
best_accuracy = 0

module = importlib.import_module(module_name)
CNN = getattr(module, "CNN")

Path(path).mkdir(exist_ok=True)

with open(path + "/" + "meta.txt", "w+") as file:
    file.write(str(params))

def START_seed():
    seed = 9
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

transform = transforms.Compose(
        [transforms.ToTensor(), 
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        transforms.Resize((160, 160), antialias=True),
        #v2.RandomResizedCrop(160, antialias=True)
        ]
    )

trainset = ImageWoof(
    root="../../", train=True, transform=transform, img_size=160
)
testset = ImageWoof(
    root="../../", train=False, transform=transform, img_size=160
)

## split into train, val, test 
print(len(trainset))     
val_size = int(0.1 * len(trainset))
print(val_size)
train_size = len(trainset) - val_size
train, val = torch.utils.data.random_split(trainset, [train_size, val_size])   

cutmix = v2.CutMix(num_classes=10, alpha=0.8)
mixup = v2.MixUp(num_classes=10, alpha=0.8)
cutmix_or_mixup = v2.RandomChoice([cutmix, mixup])

def collate_fn(batch):
    return cutmix_or_mixup(*default_collate(batch))

train_loader = torch.utils.data.DataLoader(
    train, batch_size=batch_size, shuffle=True, num_workers=4, collate_fn=collate_fn
)
val_loader = torch.utils.data.DataLoader(
    val, batch_size=batch_size, shuffle=False, num_workers=4
)    
test_loader = torch.utils.data.DataLoader(
    testset, batch_size=batch_size, shuffle=False, num_workers=1
)

# train_loader.to(device)
# val_loader.to(device)
# test_loader.to(device)

print("Trainset size: ", len(train)//batch_size)
print("Valset size: ", len(val)//batch_size)
print("Testset size: ", len(testset)//batch_size)

## Creating training loop
def train(model, epoch):
    model.train()
    train_loss = 0
    total = 0
    correct=0
    with tqdm(train_loader, unit="batch") as tepoch:
        for batch_idx, (data, target) in enumerate(tepoch):
            # send to device
            data, target = data.to(device), target.to(device)

            # test = data[:4].to('cpu')
            # images = torch.concatenate([x for x in test], dim=2)
            # plt.imshow(torch.permute(images, (1,2,0)))
            # plt.waitforbuttonpress()
    
            # clear the gradients of all optimized variables
            optimizer.zero_grad()
            # forward pass: compute predicted outputs by passing inputs to the model
            output = model(data)
            # calculate the loss
            loss = criterion(output, target)
            # backward pass: compute gradient of the loss with respect to model parameters
            loss.backward()
            # perform a single optimization step (parameter update)
            optimizer.step()
            # update running training loss
            train_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(torch.argmax(target)).sum().item()
            tepoch.set_postfix(loss=train_loss/(batch_idx+1), lr=optimizer.param_groups[0]['lr'])
        log = 'Epoch: {} - train loss: {:.4f} accuracy: {:.4f}\n'.format(epoch, train_loss/(batch_idx+1), 100.*correct/total)
        print(log)
        with open(path + "/log.txt", 'a') as file:
                file.write(log)

def validate(model):
    global best_loss, best_accuracy
    model.eval()
    
    test_loss = 0
    correct = 0
    total = 0

    with tqdm(val_loader, unit="batch") as tepoch:
        for batch_idx, (data, target) in enumerate(tepoch):
            data, target = data.to(device), target.to(device)
    
            output = model(data)
            loss = nn.CrossEntropyLoss()(output, target)
            test_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()
        if test_loss/(batch_idx+1) < best_loss:
            if(100.*correct/total > best_accuracy): 
                best_accuracy = 100.*correct/total
            print("Saving the best model...")
            best_loss = test_loss/(batch_idx+1)
            torch.save(model.state_dict(), path + '/best_model.pth')
        val_loss = test_loss/(batch_idx+1)
        log = ' val loss: {:.4f} accuracy: {:.4f} best_loss: {:.4f} best_accuracy: {:.4f}\n'.format(test_loss/(batch_idx+1), 100.*correct/total, best_loss, best_accuracy)
        print(log)
        with open(path + "/log.txt", 'a') as file:
            file.write(log)

    return val_loss

def test_best_model(model, test_loader, criterion, best_model_path):
    # Load the best model
    model.load_state_dict(torch.load(best_model_path))
    model.eval()

    test_loss = 0
    correct = 0
    total = 0

    with tqdm(test_loader, unit="batch") as tepoch:
        for batch_idx, (data, target) in enumerate(tepoch):
            data, target = data.to(device), target.to(device)

            output = model(data)
            loss = criterion(output, target)
            test_loss += loss.item()

            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

        accuracy = 100. * correct / total        
        log = 'Test loss: {:.4f} Accuracy: {:.2f}%'.format(test_loss/(batch_idx+1), accuracy)
        print(log)
        with open(path + "/log.txt", 'a') as file:
            file.write(log)     



if __name__ == "__main__":

    START_seed()
    #train_loader, val_loader, test_loader = load_dataset()

    model = CNN(num_classes=10, activation=activation)

    best_model_path = path + '/best_model.pth'  # Replace with the actual path and filename of the best model
    #if there is a model load it 
    if(os.path.exists(best_model_path)):
        model.load_state_dict(torch.load(best_model_path))

    pytorch_total_params = sum(p.numel() for p in  model.parameters())
    print('Number of parameters: {0}'.format(pytorch_total_params))

    criterion = nn.CrossEntropyLoss()
    if(params.opt == "adam"):            
        optimizer = optim.Adam(model.parameters(), lr=params.lr)
    elif(params.opt == "adamW"):
        optimizer = optim.AdamW(model.parameters(), lr=params.lr)
    elif(params.opt == "nadam"):
        optimizer = optim.NAdam(model.parameters(), lr=params.lr)
    else:
        optimizer = optim.SGD(model.parameters(), lr=params.lr)

    model.to(device)
    start = time.time()

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.1)
    for epoch in range(0, epochs):
        print("epoch number: {0}".format(epoch))
        train(model, epoch)
        val_loss = validate(model)
        scheduler.step(val_loss)
    end = time.time()
    Total_time=end-start
    print('Total training and inference time is: {0}'.format(Total_time))

    # Usage example:

    # Assuming you have a model, test_loader, and best_model_path defined

    best_model_path = path + '/best_model.pth'  # Replace with the actual path and filename of the best model
    test_best_model(model, test_loader, nn.CrossEntropyLoss(), best_model_path)