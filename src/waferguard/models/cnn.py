"""Compact spatial CNN with a fixed nine-class output order supplied by its receipt."""

import torch
from torch import nn


class WaferCNN(nn.Module):
    def __init__(self, classes: int = 9):
        super().__init__()
        blocks = []
        previous = 3
        for channels in [12, 24, 48, 64]:
            blocks.extend([nn.Conv2d(previous, channels, 3, stride=2, padding=1), nn.ReLU()])
            previous = channels
        self.spatial = nn.Sequential(*blocks)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, classes),
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        if images.ndim != 4 or images.shape[1:] != (3, 64, 64):
            raise ValueError("Expected N x 3 x 64 x 64 one-hot die-state inputs")
        return self.classifier(self.spatial(images))
