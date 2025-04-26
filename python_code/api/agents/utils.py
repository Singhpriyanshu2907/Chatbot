import json


def get_chatbot_response(client, model_name, messages, temperature=0.9, max_tokens=512):
    """
    Gets chatbot response from Mistral 7B on AWS Bedrock
    
    Args:
        client: boto3 bedrock-runtime client
        model_name: Model ID (e.g., "mistral.mistral-7b-instruct-v0:2")
        messages: List of message dicts with "role" and "content"
        temperature: Creativity control (0-1)
        max_tokens: Maximum tokens to generate
        
    Returns:
        str: Generated response
    """
    # Format conversation history for Mistral
    formatted_prompt = ""
    for message in messages:
        if message["role"] == "system":
            formatted_prompt += f"<<SYS>>\n{message['content']}\n<</SYS>>\n\n"
        elif message["role"] == "user":
            formatted_prompt += f"<s>[INST] {message['content']} [/INST]"
        elif message["role"] == "assistant":
            formatted_prompt += f" {message['content']} </s>"
    
    body = {
        "prompt": formatted_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.8  # Matching your example
    }
    
    try:
        response = client.invoke_model(
            body=json.dumps(body),
            modelId=model_name,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['outputs'][0]['text']
    
    except Exception as e:
        print(f"Error invoking model: {e}")
        return None



def get_embedding(embedding_client,model_name,text_input):
    output = embedding_client.embeddings.create(input = text_input,model=model_name)
    
    embedings = []
    for embedding_object in output.data:
        embedings.append(embedding_object.embedding)

    return embedings



def double_check_json_output(client,model_name,json_string):
    prompt = f""" You will check this json string and correct any mistakes that will make it invalid. Then you will return the corrected json string. Nothing else. 
    If the Json is correct just return it.

    if there is any text before order after the json string, remove it.
    Do Not return a single letter outside of the json string.
    Make sure that each key and value in the json string is in double quotes.
    The first thing you write should be open curly brace and the last thing you write should be close curly brace.

    you shoud check  the json string for the following text between triple backticks:

    ```
    {json_string}
    
    ```

    """

    messages = [{"role": "user", "content": prompt}]

    response = get_chatbot_response(client,model_name,messages)

    response = response.replace("`","")

    return response