import google.generativeai as genai

genai.configure(api_key='AIzaSyCxhfBUv4l6BKJUXJ35RgAIPdLkOyhQ3Go')

print("=== Available models ===")
for m in genai.list_models():
    # In newer SDK versions, supported_generation_methods is a list of strings
    methods = m.supported_generation_methods
    if 'generateContent' in methods:
        print(f"  {m.name}  (methods: {methods})")
