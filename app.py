import boto3
import streamlit as st
import logging
from botocore.exceptions import ClientError

# Logging
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS boto3 clients
bedrock_runtime_client = boto3.client("bedrock-runtime")

# VARs
model_id = "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"

# Initialize session state variables
if 'schema_description' not in st.session_state:
    st.session_state.schema_description = None
if 'tf_stack' not in st.session_state:
    st.session_state.tf_stack = None

def read_image(file_path):
    with open(file_path, "rb") as image_file:
        return image_file.read()

def read_text_file(file_path):
    with open(file_path, "rb") as prompt_file:
        return prompt_file.read().decode('utf-8')

def create_describe_message(base64_image):
    # Create the Messages API content to describe the schema (image to text) - for converse_stream() only
    explain_prompt = """
You are an AWS Certified Solutions Architect with extensive experience in interpreting and explaining AWS Architecture diagrams. Given an architecture diagram as input, your task is to provide a detailed, step-by-step description of the components and their interactions within the architecture.

When describing the architecture, follow these guidelines:

1. Identify the main components and services depicted in the diagram.
2. Explain the flow of data and requests through the architecture, starting from the client or user interface and tracing the path through various components.
3. Describe the purpose and role of each component in the architecture, highlighting its responsibilities and how it contributes to the overall system.
"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": base64_image
                        }
                    }
                },
                {
                    "text": explain_prompt
                }
            ]
        }
    ]
    return messages

def create_convert_message(schema_description: str, examples: list):
    # Create the Messages API content with TF examples
    message_content = [
        {
            "text": "Take these example Terraform code snippets as reference:"
        }
    ]
    
    for i, example in enumerate(examples, start=1):
        message_content.append({
            "text": f"""
            <example{i}>
            {example}
            </example{i}>
            """
        })
    
    message_content.append({
        "text": "Based on these examples and the following schema description, generate a Terraform stack:"
    })
    
    message_content.append({
        "text": schema_description
    })
    
    messages = [
        {
            "role": "user",
            "content": message_content
        }
    ]
    
    return messages

def get_response_stream(model_id: str, messages: list, system_prompt: str, temperature: float):
    
    """
    Model inference
    """
    try:
        response_stream = bedrock_runtime_client.converse_stream(
            modelId  = model_id,
            system   = [{
                'text': system_prompt
            }],
            messages = messages,
            inferenceConfig = {
                'maxTokens': 3000,
                'temperature': temperature,
                'topP': 1
            }
        )
        logger.info(f"Stream result: {response_stream}")
        return response_stream
    except ClientError as error:
        error_code = error.response['Error']['Code']
        error_message = error.response['Error']['Message']
        logging.info(f"Unexpected error: {error_code} - {error_message}")
    return None

def create_update_message(current_tf_stack, update_request):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": f"""
                    Here's the current Terraform stack:
                    ```hcl
                    {current_tf_stack}
                    ```
                    
                    Please apply the following updates to this Terraform stack:
                    {update_request}
                    
                    Provide the updated Terraform stack with the requested changes.
                    """
                }
            ]
        }
    ]
    return messages

def stream_response(stream_object, placeholder):
    accumulated_text = []
    input_tokens = output_tokens = total_tokens = streaming_latency = None

    for event in stream_object["stream"]:
        if 'contentBlockDelta' in event:
            if 'delta' in event["contentBlockDelta"]:
                if 'text' in event['contentBlockDelta']['delta']:
                    text_bit = event["contentBlockDelta"]["delta"]["text"]
                    accumulated_text.append(text_bit)
                    placeholder.markdown(''.join(accumulated_text))
        elif 'metadata' in event:
            metadata = event['metadata']
            if 'usage' in metadata:
                input_tokens = metadata['usage'].get('inputTokens')
                output_tokens = metadata['usage'].get('outputTokens')
                total_tokens = metadata['usage'].get('totalTokens')
            if 'metrics' in metadata:
                streaming_latency = metadata['metrics'].get('latencyMs')
    full_response = ''.join(accumulated_text)
    return full_response, input_tokens, output_tokens, total_tokens, streaming_latency

# Streamlit app
st.title('Schema to Terraform Converter')

# Step 1: Upload Schema
st.header("Step 1: Upload your schema (PNG)")
uploaded_file = st.file_uploader("Choose a schema image file", type="png")

# Step 2: Processing Result
if uploaded_file is not None:
    st.image(uploaded_file, caption='Uploaded Schema', use_column_width=True)

    if st.button('Convert to TF') or st.session_state.schema_description:
        schema = uploaded_file.getvalue()
        
        st.header("Step 2: Processing Result")
        st.subheader("Schema Description")
        # Describe step
        if not st.session_state.schema_description:
            describe_prompt = read_text_file("prompts/describe.txt")
            describe_message = create_describe_message(schema)
            describe_response = get_response_stream(model_id=model_id, messages=describe_message, system_prompt=describe_prompt, temperature=0)

            describe_placeholder = st.empty()
            describe_full_response, describe_input_tokens, describe_output_tokens, describe_total_tokens, describe_streaming_latency = stream_response(describe_response, describe_placeholder)
            
            st.session_state.schema_description = describe_full_response
        else:
            st.write(st.session_state.schema_description)
            
        st.subheader("Current Terraform Stack")
        # Convert step
        if not st.session_state.tf_stack:
            convert_prompt = read_text_file("prompts/convert.txt")
            examples = {
                read_text_file("examples/serverless_data_processing.tf"),
                read_text_file("examples/chat_websocket.tf"),
                read_text_file("examples/two_tier.tf")
            }
            convert_message = create_convert_message(schema_description = describe_full_response, examples = examples)
            convert_response = get_response_stream(model_id=model_id, messages=convert_message, system_prompt=convert_prompt, temperature=0)

            convert_placeholder = st.empty()
            convert_full_response, convert_input_tokens, convert_output_tokens, convert_total_tokens, convert_streaming_latency = stream_response(convert_response, convert_placeholder)

            st.session_state.tf_stack = convert_full_response
        else:
            st.write(st.session_state.tf_stack)

if st.session_state.tf_stack is not None:
    # Step 3: Update Terraform Stack
    st.header("Step 3: Update Terraform Stack")
    update_request = st.text_area("Enter your update request:")

    if st.button("Apply updates to TF stack"):
        if st.session_state.tf_stack:
            update_prompt = read_text_file("prompts/update.txt")
            update_message = create_update_message(st.session_state.tf_stack, update_request)
            update_response = get_response_stream(model_id=model_id, messages=update_message, system_prompt=update_prompt, temperature=0)
            update_placeholder = st.empty()
            update_full_response, update_input_tokens, update_output_tokens, update_total_tokens, update_streaming_latency = stream_response(update_response, update_placeholder)

            st.session_state.tf_stack = update_full_response
            st.markdown("[↑↑↑ Apply other updates ↑↑↑](#step-3-update-terraform-stack)")
        else:
            st.error("Please generate a Terraform stack first before applying updates.")

# Sidebar with information
st.sidebar.title("About")
st.sidebar.info("This app converts AWS architecture schema images to Terraform code leveraging AWS Bedrock")
