"""Second lightweight architecture for a measured CPU model comparison."""

from torch import nn


class WaferLiteCNN(nn.Module):
    def __init__(self, classes=9):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(3, 16, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv2d(16, 16, 3, stride=2, padding=1, groups=16),
            nn.ReLU(),
            nn.Conv2d(16, 32, 1),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, stride=2, padding=1, groups=32),
            nn.ReLU(),
            nn.Conv2d(32, 64, 1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * 8 * 8, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, classes),
        )

    def forward(self, images):
        if images.ndim != 4 or images.shape[1:] != (3, 64, 64):
            raise ValueError("Expected N x 3 x 64 x 64")
        return self.layers(images)
