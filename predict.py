import json
import torch
import torchvision.transforms as transforms
from PIL import Image
import base64
import redis
from io import BytesIO

# Create Redis connection
r = redis.Redis()

# Load the pre-trained Inception V3 model
model = torch.hub.load('pytorch/vision:v0.10.0', 'inception_v3', pretrained=True)
model.eval()

# Define the image preprocessing transform
preprocess = transforms.Compose([
    transforms.Resize((299, 299)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Function to decode and preprocess the image
def preprocess_image(image_data):
    try:
        # Decode the base64-encoded image data
        decoded_image = base64.b64decode(image_data)
        # Open the image using PIL
        image = Image.open(BytesIO(decoded_image)).convert('RGB')
        # Preprocess the image
        preprocessed_image = preprocess(image)
        return preprocessed_image.unsqueeze(0)
    except Exception as e:
        print("Error preprocessing image:", str(e))
        return None
# Function to generate predictions using the model
def generate_predictions(image):
    with torch.no_grad():

        # Forward pass through the model
        output = model(image)
        
        # Get the top 5 predicted labels and probabilities
        _, indices = torch.topk(output, 5)
        probabilities = torch.nn.functional.softmax(output, dim=1)[0]
        labels = [model.classes[idx.item()] for idx in indices[0]]
        probabilities = [prob.item() for prob in probabilities[indices[0]]]
        
        return labels, probabilities
# Continuously receive messages from the "image" queue
while True:
    # Receive message from the "image" queue
    message = r.brpop("image")
    data = json.loads(message[1])
    # Get the image data from the received message
    image_data = data["image"]
    # Preprocess the image
    preprocessed_image = preprocess_image(image_data)
    if preprocessed_image is not None:
        # Generate predictions using the model
        labels, probabilities = generate_predictions(preprocessed_image)
        # Create the message for the "prediction" queue
        message = {
            "timestamp": data["timestamp"],
            "url": data["url"],
            "predictions": [{"label": label, "probability": prob} for label, prob in zip(labels, probabilities)]
        }
        # Submit the message to the "prediction" queue
        r.lpush("prediction", json.dumps(message))