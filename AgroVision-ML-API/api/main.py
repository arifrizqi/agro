import io
import numpy as np
from PIL import Image
from skimage.transform import resize
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import storage
import tensorflow as tf
from flask import Flask, request, jsonify
from typing import Optional
from description_file import DESC
import time

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("service_account.json")
firebase_admin.initialize_app(cred)

# Initialize Google Cloud Storage
storage_client = storage.Client()

MODELS = {
    "PD-apple": {
        "path": "Plant-Diseases/Apple_MobileNetV2_model2_Based_Non_Augmented.h5",
        "class_names": ["Apple Black rot", "Apple Scab Leaf", "Apple leaf Healthy", "Apple rust leaf"],
    },
    "PD-bellpepper": {
        "path": "Plant-Diseases/BellPaper_MobileNetV2_model2_Based_Non_Augmented.h5",
        "class_names": ["Pepper bell Bacterial spot", "Pepper bell healthy"]
    },
    "PD-cherry": {
        "path": "Plant-Diseases/Cherry_MobileNetV2_model2_Based_Non_Augmented.h5",
        "class_names": ["healthy", "powdery_mildew"]
    },
    "PD-corn": {
        "path": "Plant-Diseases/Corn_MobileNetV2_model2_Based_Non_Augmented.h5",
        "class_names": ["Corn Gray leaf spot", "Corn healthy", "Corn leaf blight", "Corn rust leaf"]
    },
    "PD-grape": {
        "path": "Plant-Diseases/Grape_MobileNetV2_model2_Based_Non_Augmented.h5",
        "class_names": ["Grape Esca (Black_Measles)", "Grape Leaf blight (Isariopsis_Leaf_Spot)", "grape leaf Healthy", "grape leaf black rot"]
    },
    "PD-peach": {
        "path": "Plant-Diseases/Peach_MobileNetV2_model2_Based_Non_Augmented.h5",
        "class_names": ["Peach___Bacterial_spot", "Peach___healthy"]
    },
    "PD-potato": {
        "path": "Plant-Diseases/potato_densenet.h5",
        "class_names": ["Potato healthy", "Potato leaf early blight", "Potato leaf late blight"]
    },
    "PD-strawberry": {
        "path": "Plant-Diseases/strawberry_densenet.h5",
        "class_names": ["Strawberry___healthy", "Strawberry___Leaf_scorch"]
    },
    "PD-tomato": {
        "path": "Plant-Diseases/tomato_densenet.h5",
        "class_names": ["Tomato Early blight leaf", "Tomato Septoria leaf spot", "Tomato leaf bacterial spot", "Tomato leaf healthy", "Tomato leaf late blight", "Tomato leaf mosaic virus", "Tomato leaf yellow virus", "Tomato mold leaf", "Tomato two spotted spider mites leaf"]
    },
    "FP-bellpepper": {
        "path": "Fruit-Veg-Ripeness/BellPaper_DenseNet2_model.h5",
        "class_names": ["damaged","dried","old","ripe","unripe"]
    },
    "FP-chilepepper": {
        "path": "Fruit-Veg-Ripeness/ChilePaper_DenseNet2_model.h5",
        "class_names": ["damaged","dried","old","ripe","unripe"]
    },
    "FP-tomato": {
        "path": "Fruit-Veg-Ripeness/Tomato_DenseNet2_model.h5",
        "class_names": ["damaged","old","ripe","unripe"]
    },
    "FP-apple": {
        "path": "Fruit-Veg-Ripeness/apple_mobilenetv2.h5",
        "class_names": ["bad", "good"]
    },
    "FP-banana": {
        "path": "Fruit-Veg-Ripeness/banana_densenet121.h5",
        "class_names": ["overripe", "ripe", "rotten", "unripe"]
    },
    "FP-guava": {
        "path": "Fruit-Veg-Ripeness/guava_densenet121.h5",
        "class_names": ["bad", "good"]
    },
    "FP-lime": {
        "path": "Fruit-Veg-Ripeness/lime_densenet121.h5",
        "class_names": ["bad", "good"]
    },
    "FP-orange": {
        "path": "Fruit-Veg-Ripeness/orange_mobilenetv2.h5",
        "class_names": ["bad", "good"]
    },
    "FP-pomegranate": {
        "path": "Fruit-Veg-Ripeness/pomegranate_mobilenetv2.h5",
        "class_names": ["bad", "good"]
    }    
}

model = None

def load_model_from_storage(model_path, model_file):
    bucket_name = "agrovision-ml-model-bucket"
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(model_path)

    try:
        blob.download_to_filename(model_file)
        print(f"Blob {model_path} downloaded to {model_file}.")
    except Exception as e:
        # Handle any other exceptions that may occur during the download or model loading
        raise Exception(f"Error loading model: {str(e)}")

predictions = []
predicted_index = None
predicted_class = None
confidence = None
desc_key = []
desc_actual = None


# do prediction
@app.route("/predict", methods=["POST", "GET"])
def predict(files):
    if request.method == 'GET':
        icon= {
                "plant-disease": {
                    "1": {
                        "model": "PD-apple",
                        "title": "Apel",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Apple.png"
                    },
                    "2": {
                        "model": "PD-bellpepper",
                        "title": "Paprika",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Bellpepper.png"
                    },
                    "3": {
                        "model": "PD-cherry",
                        "title": "Ceri",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Cherry.png"
                    },
                    "4": {
                        "model": "PD-corn",
                        "title": "Jagung",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Corn.png"
                    },
                    "5": {
                        "model": "PD-grape",
                        "title": "Anggur",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/grape.png"
                    },
                    "6": {
                        "model": "PD-peach",
                        "title": "Persik",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/peach.png"
                    },
                    "7": {
                        "model": "PD-potato",
                        "title": "Kentang",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Potato.png"
                    },
                    "8": {
                        "model": "PD-strawberry",
                        "title": "Stroberi",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Strawberry.png"
                    },
                    "9": {
                        "model": "PD-tomato",
                        "title": "Tomat",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Tomato.png"
                    }
                },

                "ripeness" :{
                    "1": {
                        "model": "FP-bellpepper",
                        "title": "Paprika",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Bellpepper.png"
                    },
                    "2": {
                        "model": "FP-chilepepper",
                        "title": "Cabai",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Chillepepper.png"
                    },
                    "3": {
                        "model": "FP-tomato",
                        "title": "Tomat",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Tomato.png"
                    },
                    "4": {
                        "model": "FP-apple",
                        "title": "Apel",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Apple.png"
                    },
                    "5": {
                        "model": "FP-banana",
                        "title": "Pisang",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/banana.png"
                    },
                    "6": {
                        "model": "FP-guava",
                        "title": "Jambu Biji",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Guava.png"
                    },
                    "7": {
                        "model": "FP-lime",
                        "title": "Jeruk Nipis",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Lime.png"
                    },
                    "8": {
                        "model": "FP-orange",
                        "title": "Jeruk",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/orange.png"
                    },
                    "9": {
                        "model": "FP-pomegranate",
                        "title": "Delima",
                        "imgUrl": "https://storage.googleapis.com/icon-app/Icon/Pomagrate.png"
                    }
                }
            }
        return jsonify(icon)
    else:
        model_name = request.form.get("model", "PD-apple")
        if model_name not in MODELS:
            return {"error": f"Model '{model_name}' not found."}
            
        model_info = MODELS[model_name]
        model_path = model_info["path"]
        class_names = model_info["class_names"]
        
        # Load the model if it's not already loaded
        global model
        if model is None:
            load_model_from_storage(model_path, f"/tmp/{model_name}.h5")
            model = tf.keras.models.load_model(f"/tmp/{model_name}.h5")
        
        # Check if the file is included in the request
        if "file" not in request.files:
            return {"error": "No file uploaded."}
        
        file = request.files["file"]
        
        # Check if the file is empty
        if file.filename == "":
            return {"error": "Empty file uploaded."}
        
        # Save the file to a temporary location
        temp_file_path = f"/tmp/{file.filename}"
        file.save(temp_file_path)
        
        # Load and preprocess the image
        image = tf.keras.utils.load_img(temp_file_path, target_size=(224, 224))
        image = tf.keras.utils.img_to_array(image)
        # Resize the image to the size required by the model
        if model_name.startswith("PD-"):
            # Normalize the image
            image = image / 256.0
        else:
            image = image / 255.0
        # Expand dimensions to create a batch of size 1
        image = np.expand_dims(image, 0)
        
        # Make predictions
        predictions = model.predict(image)
        predicted_index = np.argmax(predictions[0])
        predicted_class = class_names[predicted_index]
        confidence = predictions[0][predicted_index]
        
        # Giving description to each class
        desc_key = DESC[model_name]
        desc_actual = desc_key[predicted_class]

        # Get the current timestamp in seconds
        current_timestamp = time.time()
        # Convert timestamp to local time
        current_local_time = time.ctime(current_timestamp)
        
        # Save the prediction to Firebase Firestore
        db = firestore.client()
        uid = request.form.get("uid", "Not0xA8TQUbQOMONJWTYos4cPCv1")  # Replace with the appropriate user ID, default value "Not0xA8TQUbQOMONJWTYos4cPCv1"
        result = {"class": predicted_class, "confidence": float(confidence), "description": (desc_actual), "time": current_local_time}
        
        predictions_ref = db.collection("predictions")
        user_predictions_ref = predictions_ref.document(uid)
        user_predictions_ref.set(result)
        
        return {"class": predicted_class, "confidence": float(confidence), "description": (desc_actual), "time": current_local_time}