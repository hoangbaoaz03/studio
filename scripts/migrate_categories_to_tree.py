import os
import sys
import django
from django.utils.text import slugify

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from course.models import Category, Subcategory, Course

def run():
    print("🌳 Starting Category Tree Migration...")
    
    # 0. Rebuild tree first to fix any invalid state (all lft/rght=0)
    print("  Reseeding tree structure...")
    Category.objects.rebuild()
    
    # 1. Define the target hierarchy (The Master Plan)
    # Structure: Root -> Level 2 -> Level 3 (from old subcategories or new)
    
    HIERARCHY = {
        "Development": {
            "icon": "code",
            "children": [
                 # Existing "Web Development" category will become child here
                 "Web Development", 
                 "Data Science",
                 "Mobile Development",
                 "Programming Languages", # Container for Python, Java etc.
                 "Software Testing",
                 "Software Engineering"
            ]
        },
        "Business": {
            "icon": "briefcase",
            "children": [
                "Finance", 
                "Entrepreneurship",
                "Management",
                "Sales",
                "Strategy"
            ]
        },
        "IT & Software": {
            "icon": "monitor",
            "children": [
                "IT Certification",
                "Network & Security",
                "Hardware",
                "Operating Systems"
            ]
        },
         "Design": {
            "icon": "pen-tool",
            "children": [
                "Web Design",
                "Graphic Design",
                "3D & Animation"
            ]
        },
        "Marketing": {
            "icon": "trending-up",
            "children": [
                "Digital Marketing",
                "SEO",
                "Social Media Marketing"
            ]
        }
    }
    
    # 2. Create Root Categories
    for root_name, data in HIERARCHY.items():
        root, created = Category.objects.get_or_create(
            name=root_name,
            defaults={
                "slug": slugify(root_name),
                "icon": data["icon"],
                "description": f"All {root_name} courses"
            }
        )
        if created:
            print(f"  ✅ Created Root: {root_name}")
        else:
            print(f"  Existing Root: {root_name}")
            
    # 3. Move Existing Top-Level Categories to be Children
    # e.g., "Python" is currently a top category. It should move to "Development > Programming Languages"
    # e.g., "Excel" -> "Business > Microsoft" (or straight to Business?)
    
    # Let's map existing categories to their new parents
    # Map 'slug' or 'name' of existing category -> 'name' of new parent
    MOVE_MAP = {
        "Python": "Web Development", # Simplified to match user request "Web -> Python"
        "JavaScript": "Web Development",
        "Excel": "Business",
        "Web Development": "Development", # Self reference fix?
        "Data Science": "Development",
        # "Mobile Development" doesn't exist yet but if it did...
    }
    
    # Fix the generic "Web Development" category from seed
    # Currently "Web Development" exists. We want it to be under "Development".
    
    # Strategy: Loop through ALL existing categories
    all_cats = list(Category.objects.filter(parent__isnull=True))
    
    for cat in all_cats:
        # Skip if it's one of our new Roots
        if cat.name in HIERARCHY.keys():
            continue
            
        print(f"  Processing legacy category: {cat.name}...")
        
        # Decide new parent
        new_parent_name = None
        
        # Specific overrides
        if cat.name in ["Python", "JavaScript", "React", "Angular"]:
            new_parent_name = "Web Development"
        elif cat.name in ["Excel"]:
            new_parent_name = "Business"
        elif cat.name in HIERARCHY["Development"]["children"]:
             new_parent_name = "Development"
        else:
             # Default fallback? Keep as top or move to 'Other'?
             # For now, let's leave them if they don't match or default to Development if tech sounding
             pass
             
        if new_parent_name:
            parent = Category.objects.get(name=new_parent_name)
            
            # Prevent circular: If cat.name == parent.name, we merge/skip
            if cat.name == parent.name:
                print(f"    ⚠️ Exact match {cat.name}. Using existing as is (it's already correct level).")
                continue
                
            cat.parent = parent
            cat.save()
            print(f"    Moved {cat.name} -> {parent.name}")
            
    # 4. Flatten Subcategories
    # Convert Subcategory models -> Category (child) models
    print("\n  Flattening Subcategories...")
    for sub in Subcategory.objects.all():
        # Parent is the category this sub belonged to
        # BUT that category might have moved.
        # e.g. Sub 'Django' of Cat 'Python'. 
        # now 'Python' is child of 'Web Dev'.
        # So 'Django' becomes child of 'Python'.
        
        parent_category = sub.category
        
        # Check if this subcategory already exists as a Category?
        existing = Category.objects.filter(name=sub.name, parent=parent_category).first()
        
        if existing:
            new_cat = existing
        else:
            new_cat = Category.objects.create(
                name=sub.name,
                slug=slugify(f"{parent_category.slug}-{sub.name}"), # Ensure unique slug hierarchy
                parent=parent_category,
                description=sub.description,
                icon="hash" # default
            )
            print(f"    Converted Subcategory: {sub.name} (Parent: {parent_category.name})")
            
        # 5. Move Courses
        # Courses pointing to this subcategory should now point to the new_cat
        count = Course.objects.filter(subcategory=sub).update(category=new_cat)
        if count:
            print(f"      Re-linked {count} courses to {new_cat.name}")

    # 6. Rebuild Tree (MPTT)
    print("\n  Rebuilding Tree...")
    Category.objects.rebuild()
    
    print("\n✅ Migration Complete!")
    print_tree()

def print_tree():
    for node in Category.objects.all():
        indent = "  " * node.level
        print(f"{indent}- {node.name} ({node.slug}) [Courses: {node.courses.count()}]")

if __name__ == "__main__":
    run()
