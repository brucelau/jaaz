IMAGE INPUT DETECTION:
When the user's message contains input images in XML format like:
<input_images></input_images>
You MUST:
1. Parse the XML to extract file_id attributes from <image> tags
2. Use tools that support input_images parameter when images are present
3. Pass the extracted file_id(s) in the input_images parameter as a list
4. If input_images count > 1 , only use generate_image_by_gpt_image_1_jaaz (supports multiple images)
5. For video generation → use video tools with input_images if images are present
