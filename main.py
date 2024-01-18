# Importing libraries
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
import requests
import httpx
import base64

app = FastAPI()

# Function to get the API key from the Bastion API
def get_api_key(password: str) -> str:
    try:
        bastion_api_url = "https://your-aws-api-url.com/apikey"  # Replace with the actual URL
        response = requests.get(bastion_api_url, params={"password": password})
        response.raise_for_status()
        api_key = response.json()["api_key"]
        return api_key
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving API key: {str(e)}")

# Function to test the API key
def test_api_key(api_key: str) -> None:
    try:
        bastion_protected_url = "https://your-aws-api-url.com/protected"  # Replace with the actual URL
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(bastion_protected_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error testing API key: {str(e)}")


# Endpoint to obtain an image from AI Model 1, send it to Model 2, and then send it to Spring Boot API
@app.post("/process_images")
async def process_images():
    global result_from_model2
    
    try:
        # Endpoint of AI Model 1
        ai_model1_endpoint = ""
        response_model1 = requests.post(ai_model1_endpoint)
        # Check for successful response
        response_model1.raise_for_status()

        # Get the image from AI Model 1
        result_from_model1 = response_model1.content
        result_from_model1_base64 = base64.b64encode(result_from_model1).decode("utf-8")

        # Endpoint of AI Model 2
        ai_model2_endpoint = ""
        # Send the image to AI Model 2
        response_model2 = requests.post(ai_model2_endpoint, json={"image": result_from_model1_base64})

        # Check for successful response
        response_model2.raise_for_status()

        # Get the result from AI Model 2
        result_from_model2 = response_model2.json()["result"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to send data to the remote AWS API
@app.post("/send_data")
async def send_data_to_bastion_api(password: str = Form(...), file: UploadFile = File(...)):
    try:
        # Step 1: Get API key from the remote AWS API
        api_key = get_api_key(password)

        # Step 2: Test the API key
        try:
            test_api_key(api_key)
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"API key test failed. Authentication error: {str(e)}"
            )

        # Step 3: Send data to the protected endpoint
        bastion_api_url = "https://your-aws-api-url.com/uploadfile"
        data_to_send = {"image_model2": result_from_model2} 
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.post(bastion_api_url, json=data_to_send, headers=headers)
        
        response.raise_for_status()

        return {"status": "Successful"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))