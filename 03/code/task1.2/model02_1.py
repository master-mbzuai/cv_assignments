import torch
from torch import nn


class CNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()

class CNN(nn.Module):
    def __init__(self, num_classes=10, activation=nn.GELU):
        super().__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(3, 32, 3, 1),
            activation,  
            nn.MaxPool2d(2),
            #####
            nn.Conv2d(32, 64, 3, 1),
            activation,
            nn.Conv2d(64, 64, 3, 1),
            activation,
            nn.MaxPool2d(2),
            #####
            nn.Conv2d(64, 128, 3, 1),
            activation,
            nn.Conv2d(128, 128, 3, 1),
            activation,
            nn.MaxPool2d(2),
            ####
            nn.Conv2d(128, 256, 3, 1),
            activation,
            nn.Conv2d(256, 256, 3, 1),
            activation,
            nn.MaxPool2d(2),
            ####
            nn.Conv2d(256, 512, 3, 1),
            activation,
            nn.AdaptiveAvgPool2d(
                output_size=1,
            ),
            nn.Flatten()
        )
        self.classifier = nn.Sequential(
            nn.Linear(512, 256),            
            activation,
            nn.Linear(256, 128),            
            activation,
            nn.Linear(128, 64),            
            activation,
            nn.Linear(64, num_classes),
        )
        
    def forward(self, x):
        features = self.feature_extractor(x)
        features = torch.flatten(features, start_dim=1)
        out = self.classifier(features)
        return out

    def num_of_params(self):
        total = 0
        for layer_params in self.feature_extractor.parameters():
            total += layer_params.numel()
        for layer_params in self.classifier.parameters():
            total += layer_params.numel()
        return total
