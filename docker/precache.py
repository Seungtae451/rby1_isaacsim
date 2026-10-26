"""Build-time public metric weights; runtime must work with network disabled."""
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity

LearnedPerceptualImagePatchSimilarity(net_type='vgg', normalize=True)
print('VGG/LPIPS metric weights cached for offline reconstruction.')
