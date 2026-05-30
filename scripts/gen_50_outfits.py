import random
import uuid

genders = ["женское", "мужское"]
occasions = ["love-story", "семейная съёмка", "беременность", "индивидуальная", "lookbook", "контент для соцсетей"]
styles = ["минимализм", "классика", "old money", "casual", "романтика"]
seasons = ["весна", "лето", "осень", "зима"]
colors = ["черный", "белый", "бежевый", "синий", "красный", "серый", "коричневый"]

sql = ["-- Seed 50 random outfits\n"]

for i in range(1, 51):
    gender = random.choice(genders)
    occasion = random.sample(occasions, random.randint(1, 3))
    style = random.sample(styles, random.randint(1, 2))
    season = random.sample(seasons, random.randint(1, 2))
    color = random.sample(colors, random.randint(1, 2))
    
    title = f"Образ {i}: {', '.join(style).capitalize()}"
    desc = f"Прекрасный {gender} образ для {' и '.join(occasion)}. Подходит на {', '.join(season)}."
    
    # We use a CTE or just variables? Better just plain INSERTs
    # outfit_images needs the ID of the inserted outfit. We can use generated uuid or just currval?
    # Actually, we can use a DO block or just insert and then get ID.
    # To keep it simple:
    sql.append(f"""
WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    '{title}', 
    '{desc}', 
    '{gender}', 
    '{', '.join(color)}', 
    '{', '.join(style)}', 
    '{', '.join(season)}', 
    '{', '.join(occasion)}', 
    true, 
    {i}
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit{i}/800/800', 0 FROM new_outfit;
""")

with open("supabase/migrations/0014_seed_50_outfits.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql))
