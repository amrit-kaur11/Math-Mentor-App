def process_text(user_input = 'str'):
    """
    Handles plain text input from the user.

    Args: 
        user_input (str): Raw text entered by the user

    Return: 
        tuple:
            - cleaned_text (str)
            - confidence (float)
    
    """

    if user_input is None:
        return None, 0.0    
    
    #Basic Cleaning

    cleaned_text = user_input.strip()

    if cleaned_text ==  "":
        return None, 0.0
    
    #Typed text is assumed to be fully confident
    confidence = 1.0
    
    return cleaned_text, confidence
