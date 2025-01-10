# -*- coding: utf-8 -*-
"""dashboard.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1aRxFwsWCuasc6pOUH2iSpP86GqERj46M
"""
import os
import json
import base64

# Image processing
from PIL import Image, ImageDraw, ImageFont

# Data manipulation
import pandas as pd
from sentence_transformers import SentenceTransformer
import anthropic
from pinecone import Pinecone

# Set environment variables
os.environ["ANTHROPIC_API_KEY"] = "${ANTHROPIC_API_KEY}"
os.environ["PINECONE_API_KEY"] = "${PINECONE_API_KEY}"

# Initialize Pinecone and Anthropic
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Pinecone setup
index_name = "nervous"
index = pinecone_client.Index(index_name)

# Load embedding model
embedding_model = SentenceTransformer("all-mpnet-base-v2")

# Function to generate 1536-dimensional embeddings
def get_embedding(text):
    try:
        embedding = embedding_model.encode(text).tolist()
        return embedding + embedding  # Double the vector to make it 1536 dimensions
    except Exception as e:
        print(f"Failed to generate embedding: {str(e)}")
        return None

# Extract images with captions from JSON
def extract_images_with_captions(json_data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    images = [item for item in json_data if item["type"] == "Image"]
    captions = [item for item in json_data if item["type"] == "Caption"]

    for idx, image in enumerate(images):
        binary_data = image.get("binary_representation")
        if binary_data:
            try:
                # Decode Base64 and save the image
                img_data = base64.b64decode(binary_data)
                image_size = image["properties"]["image_size"]
                image_mode = image["properties"]["image_mode"]
                img = Image.frombytes(image_mode, tuple(image_size), img_data)

                # Find associated caption
                caption_text = "No caption available."
                image_bbox = image["bbox"]
                for caption in captions:
                    caption_bbox = caption["bbox"]
                    if (
                        caption_bbox[0] >= image_bbox[0]
                        and caption_bbox[2] <= image_bbox[2]
                        and caption_bbox[1] >= image_bbox[3]
                    ):
                        caption_text = caption["text_representation"]
                        break

                # Add caption to the image
                if caption_text:
                    new_height = img.height + 40
                    new_img = Image.new("RGB", (img.width, new_height), "white")
                    new_img.paste(img, (0, 0))
                    draw = ImageDraw.Draw(new_img)
                    font = ImageFont.load_default()
                    draw.text((10, img.height + 10), caption_text, fill="black", font=font)
                    img = new_img

                # Save the image
                img.save(os.path.join(output_dir, f"image_with_caption_{idx + 1}.png"))
                print(f"Image {idx + 1} with caption saved successfully!")
            except Exception as e:
                print(f"Failed to decode image {idx + 1}: {e}")
        else:
            print(f"No binary data for image {idx + 1}.")

# Extract tables with captions from JSON
def extract_tables_with_captions(json_data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    tables = [item for item in json_data if item["type"] == "table"]
    captions = [item for item in json_data if item["type"] == "Caption"]

    for idx, table in enumerate(tables):
        try:
            cells = table["table"]["cells"]
            rows = {}
            for cell in cells:
                row_idx = cell["rows"][0]
                col_idx = cell["cols"][0]
                content = cell.get("content", "")
                if row_idx not in rows:
                    rows[row_idx] = {}
                rows[row_idx][col_idx] = content

            # Create a pandas DataFrame
            df = pd.DataFrame.from_dict(rows, orient="index").sort_index(axis=1)

            # Find associated caption
            caption_text = "No caption available."
            table_bbox = table["bbox"]
            for caption in captions:
                caption_bbox = caption["bbox"]
                if (
                    caption_bbox[0] >= table_bbox[0]
                    and caption_bbox[2] <= table_bbox[2]
                    and caption_bbox[1] >= table_bbox[3]
                ):
                    caption_text = caption["text_representation"]
                    break

            # Save the table and caption
            table_path = os.path.join(output_dir, f"table_with_caption_{idx + 1}.csv")
            df.to_csv(table_path, index=False)
            if caption_text:
                with open(table_path.replace(".csv", ".txt"), "w") as caption_file:
                    caption_file.write(caption_text)
            print(f"Table {idx + 1} with caption saved successfully!")
        except Exception as e:
            print(f"Failed to process table {idx + 1}: {e}")

# Upload extracted data to Pinecone
def upload_to_pinecone(output_dir):
    id_counter = 1
    for file in os.listdir(output_dir):
        if file.endswith(".png") or file.endswith(".csv"):
            file_path = os.path.join(output_dir, file)
            metadata = {"type": "image" if file.endswith(".png") else "table"}
            if file.endswith(".png"):
                # Add image caption
                caption_path = file_path.replace(".png", ".txt")
                if os.path.exists(caption_path):
                    with open(caption_path, "r") as f:
                        metadata["text_representation"] = f.read()
                else:
                    metadata["text_representation"] = "No description available for this image."
            elif file.endswith(".csv"):
                # Add table data and caption
                df = pd.read_csv(file_path)
                metadata["table_data"] = df.to_json(orient="split")
                caption_path = file_path.replace(".csv", ".txt")
                if os.path.exists(caption_path):
                    with open(caption_path, "r") as f:
                        metadata["text_representation"] = f.read()
                else:
                    metadata["text_representation"] = "No description available for this table."
            # Generate embedding
            embedding = get_embedding(metadata.get("text_representation", "No description available."))
            if embedding:
                # Upload to Pinecone
                index.upsert([{"id": f"item_{id_counter}", "values": embedding, "metadata": metadata}])
                id_counter += 1
                print(f"Uploaded {file} to Pinecone.")
            else:
                print(f"Skipping {file} due to embedding failure.")

# Query Pinecone and use Claude
def ask_claude(user_input):
    try:
        # Generate embedding for the question
        query_embedding = get_embedding(user_input)

        if not query_embedding:
            return "Failed to generate embedding for the input question."

        # Query Pinecone for relevant context
        query_result = index.query(vector=query_embedding, top_k=5, include_metadata=True)

        # Extract context from Pinecone results
        context_list = [
            item["metadata"].get("text_representation", "No description available.")
            for item in query_result["matches"]
        ]
        context = "\n".join(context_list)

        # Combine the context with user input
        prompt = anthropic.HUMAN_PROMPT + f"Context: {context}\n\nUser Question: {user_input}" + anthropic.AI_PROMPT

        # Send the prompt to Claude
        message = anthropic_client.completions.create(
            model="claude-2",
            max_tokens_to_sample=1000,
            temperature=0,
            prompt=prompt
        )

        # Return Claude's response
        return message.completion

    except Exception as e:
        print(f"Error querying Claude: {str(e)}")
        return None

# Main script
if __name__ == "__main__":
    json_path = "/content/Digestive_System_508-bbox.json"  # Replace with your JSON file path
    output_dir = "data"

    # Load JSON data
    with open(json_path, "r") as f:
        json_data = json.load(f)

    # Extract images and tables with captions
    extract_images_with_captions(json_data, output_dir)
    extract_tables_with_captions(json_data, output_dir)

    # Upload extracted data to Pinecone
    upload_to_pinecone(output_dir)

    # Ask questions in a loop
    print("Type 'quit' or 'exit' to stop.")
    while True:
        user_question = input("Enter your question: ")
        if user_question.lower() in ["quit", "exit"]:
            print("Exiting. Goodbye!")
            break
        response = ask_claude(user_question)
        if response:
            print(response)
        else:
            print("No response from Claude.")