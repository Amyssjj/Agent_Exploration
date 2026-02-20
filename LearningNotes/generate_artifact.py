import os

files = [
    "architecture_guide.md",
    "skills_understanding.md",
    "video_analysis_understanding.md",
    "token_efficiency_evaluation.md",
    "session_architecture.md",
    "system_prompt_structure.md",
    "exec_approval_implementation_plan.md"
]

base_dir = "/Volumes/Motus_SSD/mac_mini/ClawdBot_Github/openclaw/UnderStanding"
output_path = "/Users/jingshi/.gemini/antigravity/brain/2fd9b450-e67f-413f-848c-d7165f7b5c53/openclaw_documentation_viewer.md"

with open(output_path, "w") as outfile:
    outfile.write("````carousel\n")
    
    for i, fname in enumerate(files):
        file_path = os.path.join(base_dir, fname)
        if os.path.exists(file_path):
            with open(file_path, "r") as infile:
                outfile.write(infile.read())
            
            # Add separator if not the last file
            if i < len(files) - 1:
                outfile.write("\n\n<!-- slide -->\n\n")
    
    outfile.write("\n````")

print(f"Generated {output_path}")
