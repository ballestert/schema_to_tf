# Schema to Terraform Converter

This Streamlit application converts AWS architecture schema images to Terraform code and allows for dynamic updates, leveraging AWS Bedrock and Claude 3.5 Sonnet.

## Features

- Upload AWS architecture schema images (PNG format)
- Generate detailed descriptions of the uploaded schemas
- Convert schema descriptions to Terraform code
- Update generated Terraform code based on user requests
- Real-time streaming of AI-generated responses

## Prerequisites

- Python 3.7+
- AWS account with access to Bedrock and the required base models (default model is Claude 3.5 Sonnet) 
- AWS CLI configured with appropriate credentials (default model requires EU AWS Region)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/ballestert/schema_to_tf.git
   cd schema_to_tf
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Ensure your AWS CLI is configured with the necessary credentials to access and invoke Bedrock models.

2. Update the `model_id` variable in the script if you're using a different model.
   - Default model is Claude 3.5 Sonnet EU (cross-region Europe inference profile) 

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL provided by Streamlit (`http://localhost:8501`).

3. Use the app through the following steps:
   - Upload an AWS architecture schema image (PNG format)
   - Click "Process Schema" to generate a description and Terraform code
   - View the results in the "Results" section
   - If required, enter update requests in the "Update Terraform Stack" section and click "Apply Updates" to modify the Terraform code

## Project Structure

- `app.py`: Main Streamlit application script
- `prompts/`: Directory containing system prompts text files for the describe, convert and update inferences
- `examples/`: Directory containing example Terraform code

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses AWS Bedrock and Claude 3.5 Sonnet for natural language processing and code generation.
- Streamlit is used for the web application framework.