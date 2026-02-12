import numpy as np
from PIL import Image
import easyocr

#Initialize the OCR reader once
reader = easyocr.Reader(['en'], gpu=False)


def process_image(image_file):
    """
    Processes an uploaded image and extracts text using OCR.

    Args:
        image_file = uploaded image file object

    Return:
        Tuple:
            - extracted_text (str)
            - confidence (float)    
    """
    try: 
        #Load image using PTL
        image = Image.open(image_file).convert("RGB")
        image_np = np.array(image)

        #Perform OCR
        results = reader.readtext(image_np)
        
        if not results:
            return None, 0.0
        
        extracted_texts = []
        confidences = []

        for bbox, text, conf in results:
            extracted_texts.append(text)
            confidences.append(conf)

        #Combine all detected text
        extracted_text = " ". join(extracted_texts)

        #Average confidence
        confidence = sum(confidences)/len(confidences)

        #OCR
        MIN_TEXT_LENGTH = 5

        #Remove spacing to check actual text length
        content_length = len(extracted_text.replace(" ",""))

        if content_length < MIN_TEXT_LENGTH:
            #Force low confidence to trigger the hitl
            confidence = 0.0

        return extracted_text.strip(), confidence
    
    except Exception as e:
        #OCR failure fallback
        return None, 0.0