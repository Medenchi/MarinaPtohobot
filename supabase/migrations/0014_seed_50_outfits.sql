-- Seed 50 random outfits


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 1: Минимализм, casual', 
    'Прекрасный мужское образ для lookbook. Подходит на зима.', 
    'мужское', 
    'красный, серый', 
    'минимализм, casual', 
    'зима', 
    'lookbook', 
    true, 
    1
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit1/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 2: Романтика, минимализм', 
    'Прекрасный мужское образ для семейная съёмка. Подходит на осень.', 
    'мужское', 
    'красный', 
    'романтика, минимализм', 
    'осень', 
    'семейная съёмка', 
    true, 
    2
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit2/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 3: Old money, романтика', 
    'Прекрасный мужское образ для love-story и беременность и lookbook. Подходит на осень.', 
    'мужское', 
    'черный, серый', 
    'old money, романтика', 
    'осень', 
    'love-story, беременность, lookbook', 
    true, 
    3
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit3/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 4: Классика', 
    'Прекрасный мужское образ для семейная съёмка и lookbook и беременность. Подходит на осень.', 
    'мужское', 
    'белый, синий', 
    'классика', 
    'осень', 
    'семейная съёмка, lookbook, беременность', 
    true, 
    4
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit4/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 5: Минимализм, классика', 
    'Прекрасный женское образ для lookbook и семейная съёмка и индивидуальная. Подходит на весна, лето.', 
    'женское', 
    'серый', 
    'минимализм, классика', 
    'весна, лето', 
    'lookbook, семейная съёмка, индивидуальная', 
    true, 
    5
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit5/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 6: Минимализм, old money', 
    'Прекрасный женское образ для lookbook и индивидуальная. Подходит на зима, лето.', 
    'женское', 
    'серый, синий', 
    'минимализм, old money', 
    'зима, лето', 
    'lookbook, индивидуальная', 
    true, 
    6
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit6/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 7: Casual', 
    'Прекрасный мужское образ для контент для соцсетей и беременность и семейная съёмка. Подходит на осень.', 
    'мужское', 
    'коричневый, серый', 
    'casual', 
    'осень', 
    'контент для соцсетей, беременность, семейная съёмка', 
    true, 
    7
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit7/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 8: Минимализм, casual', 
    'Прекрасный мужское образ для контент для соцсетей и семейная съёмка. Подходит на лето.', 
    'мужское', 
    'серый, синий', 
    'минимализм, casual', 
    'лето', 
    'контент для соцсетей, семейная съёмка', 
    true, 
    8
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit8/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 9: Романтика, old money', 
    'Прекрасный мужское образ для индивидуальная и семейная съёмка. Подходит на весна, зима.', 
    'мужское', 
    'серый', 
    'романтика, old money', 
    'весна, зима', 
    'индивидуальная, семейная съёмка', 
    true, 
    9
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit9/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 10: Минимализм, casual', 
    'Прекрасный женское образ для контент для соцсетей и love-story и беременность. Подходит на осень, весна.', 
    'женское', 
    'белый, красный', 
    'минимализм, casual', 
    'осень, весна', 
    'контент для соцсетей, love-story, беременность', 
    true, 
    10
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit10/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 11: Old money, минимализм', 
    'Прекрасный женское образ для беременность и lookbook. Подходит на зима, лето.', 
    'женское', 
    'серый, красный', 
    'old money, минимализм', 
    'зима, лето', 
    'беременность, lookbook', 
    true, 
    11
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit11/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 12: Casual, классика', 
    'Прекрасный мужское образ для индивидуальная и семейная съёмка и контент для соцсетей. Подходит на зима.', 
    'мужское', 
    'белый, серый', 
    'casual, классика', 
    'зима', 
    'индивидуальная, семейная съёмка, контент для соцсетей', 
    true, 
    12
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit12/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 13: Классика, casual', 
    'Прекрасный мужское образ для беременность и lookbook. Подходит на осень, зима.', 
    'мужское', 
    'белый', 
    'классика, casual', 
    'осень, зима', 
    'беременность, lookbook', 
    true, 
    13
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit13/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 14: Минимализм', 
    'Прекрасный женское образ для беременность. Подходит на осень.', 
    'женское', 
    'белый, коричневый', 
    'минимализм', 
    'осень', 
    'беременность', 
    true, 
    14
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit14/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 15: Классика, романтика', 
    'Прекрасный женское образ для индивидуальная и семейная съёмка. Подходит на зима.', 
    'женское', 
    'белый', 
    'классика, романтика', 
    'зима', 
    'индивидуальная, семейная съёмка', 
    true, 
    15
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit15/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 16: Минимализм, романтика', 
    'Прекрасный мужское образ для контент для соцсетей. Подходит на зима, лето.', 
    'мужское', 
    'синий', 
    'минимализм, романтика', 
    'зима, лето', 
    'контент для соцсетей', 
    true, 
    16
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit16/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 17: Casual', 
    'Прекрасный мужское образ для беременность и контент для соцсетей. Подходит на осень.', 
    'мужское', 
    'коричневый', 
    'casual', 
    'осень', 
    'беременность, контент для соцсетей', 
    true, 
    17
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit17/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 18: Классика, минимализм', 
    'Прекрасный мужское образ для беременность. Подходит на весна.', 
    'мужское', 
    'синий, коричневый', 
    'классика, минимализм', 
    'весна', 
    'беременность', 
    true, 
    18
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit18/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 19: Casual, old money', 
    'Прекрасный мужское образ для love-story. Подходит на лето, весна.', 
    'мужское', 
    'красный', 
    'casual, old money', 
    'лето, весна', 
    'love-story', 
    true, 
    19
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit19/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 20: Классика, casual', 
    'Прекрасный женское образ для контент для соцсетей и lookbook. Подходит на осень, весна.', 
    'женское', 
    'красный', 
    'классика, casual', 
    'осень, весна', 
    'контент для соцсетей, lookbook', 
    true, 
    20
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit20/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 21: Романтика', 
    'Прекрасный женское образ для love-story. Подходит на зима, весна.', 
    'женское', 
    'бежевый, красный', 
    'романтика', 
    'зима, весна', 
    'love-story', 
    true, 
    21
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit21/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 22: Casual, old money', 
    'Прекрасный мужское образ для беременность и контент для соцсетей и индивидуальная. Подходит на зима.', 
    'мужское', 
    'белый', 
    'casual, old money', 
    'зима', 
    'беременность, контент для соцсетей, индивидуальная', 
    true, 
    22
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit22/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 23: Минимализм', 
    'Прекрасный мужское образ для контент для соцсетей. Подходит на лето.', 
    'мужское', 
    'черный', 
    'минимализм', 
    'лето', 
    'контент для соцсетей', 
    true, 
    23
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit23/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 24: Casual', 
    'Прекрасный мужское образ для индивидуальная. Подходит на зима.', 
    'мужское', 
    'бежевый', 
    'casual', 
    'зима', 
    'индивидуальная', 
    true, 
    24
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit24/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 25: Casual, романтика', 
    'Прекрасный женское образ для беременность и love-story и индивидуальная. Подходит на лето, осень.', 
    'женское', 
    'бежевый, серый', 
    'casual, романтика', 
    'лето, осень', 
    'беременность, love-story, индивидуальная', 
    true, 
    25
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit25/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 26: Casual', 
    'Прекрасный мужское образ для love-story. Подходит на лето.', 
    'мужское', 
    'бежевый, красный', 
    'casual', 
    'лето', 
    'love-story', 
    true, 
    26
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit26/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 27: Casual', 
    'Прекрасный мужское образ для love-story и индивидуальная и беременность. Подходит на лето.', 
    'мужское', 
    'коричневый', 
    'casual', 
    'лето', 
    'love-story, индивидуальная, беременность', 
    true, 
    27
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit27/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 28: Романтика, casual', 
    'Прекрасный женское образ для lookbook и беременность и love-story. Подходит на зима, весна.', 
    'женское', 
    'красный', 
    'романтика, casual', 
    'зима, весна', 
    'lookbook, беременность, love-story', 
    true, 
    28
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit28/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 29: Casual', 
    'Прекрасный мужское образ для беременность и семейная съёмка и lookbook. Подходит на зима.', 
    'мужское', 
    'синий', 
    'casual', 
    'зима', 
    'беременность, семейная съёмка, lookbook', 
    true, 
    29
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit29/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 30: Романтика', 
    'Прекрасный мужское образ для индивидуальная и беременность. Подходит на зима.', 
    'мужское', 
    'красный, серый', 
    'романтика', 
    'зима', 
    'индивидуальная, беременность', 
    true, 
    30
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit30/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 31: Casual', 
    'Прекрасный мужское образ для контент для соцсетей и love-story. Подходит на лето, весна.', 
    'мужское', 
    'синий, белый', 
    'casual', 
    'лето, весна', 
    'контент для соцсетей, love-story', 
    true, 
    31
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit31/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 32: Романтика', 
    'Прекрасный мужское образ для семейная съёмка и беременность. Подходит на осень.', 
    'мужское', 
    'серый, белый', 
    'романтика', 
    'осень', 
    'семейная съёмка, беременность', 
    true, 
    32
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit32/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 33: Романтика, классика', 
    'Прекрасный мужское образ для беременность и love-story. Подходит на осень.', 
    'мужское', 
    'белый, черный', 
    'романтика, классика', 
    'осень', 
    'беременность, love-story', 
    true, 
    33
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit33/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 34: Old money', 
    'Прекрасный женское образ для семейная съёмка. Подходит на весна.', 
    'женское', 
    'черный', 
    'old money', 
    'весна', 
    'семейная съёмка', 
    true, 
    34
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit34/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 35: Классика', 
    'Прекрасный мужское образ для индивидуальная. Подходит на лето.', 
    'мужское', 
    'синий, белый', 
    'классика', 
    'лето', 
    'индивидуальная', 
    true, 
    35
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit35/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 36: Casual, old money', 
    'Прекрасный женское образ для контент для соцсетей. Подходит на лето, осень.', 
    'женское', 
    'синий, красный', 
    'casual, old money', 
    'лето, осень', 
    'контент для соцсетей', 
    true, 
    36
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit36/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 37: Романтика', 
    'Прекрасный женское образ для семейная съёмка. Подходит на осень, весна.', 
    'женское', 
    'синий', 
    'романтика', 
    'осень, весна', 
    'семейная съёмка', 
    true, 
    37
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit37/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 38: Классика', 
    'Прекрасный мужское образ для индивидуальная и беременность. Подходит на лето, осень.', 
    'мужское', 
    'красный, белый', 
    'классика', 
    'лето, осень', 
    'индивидуальная, беременность', 
    true, 
    38
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit38/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 39: Минимализм, классика', 
    'Прекрасный женское образ для love-story и lookbook. Подходит на зима, лето.', 
    'женское', 
    'черный', 
    'минимализм, классика', 
    'зима, лето', 
    'love-story, lookbook', 
    true, 
    39
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit39/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 40: Минимализм, классика', 
    'Прекрасный женское образ для lookbook и контент для соцсетей. Подходит на осень.', 
    'женское', 
    'серый, коричневый', 
    'минимализм, классика', 
    'осень', 
    'lookbook, контент для соцсетей', 
    true, 
    40
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit40/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 41: Old money, классика', 
    'Прекрасный мужское образ для контент для соцсетей. Подходит на лето.', 
    'мужское', 
    'серый', 
    'old money, классика', 
    'лето', 
    'контент для соцсетей', 
    true, 
    41
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit41/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 42: Casual, old money', 
    'Прекрасный мужское образ для беременность. Подходит на зима.', 
    'мужское', 
    'белый', 
    'casual, old money', 
    'зима', 
    'беременность', 
    true, 
    42
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit42/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 43: Классика', 
    'Прекрасный женское образ для love-story и семейная съёмка и lookbook. Подходит на лето, зима.', 
    'женское', 
    'коричневый', 
    'классика', 
    'лето, зима', 
    'love-story, семейная съёмка, lookbook', 
    true, 
    43
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit43/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 44: Old money', 
    'Прекрасный женское образ для индивидуальная и lookbook. Подходит на лето.', 
    'женское', 
    'белый', 
    'old money', 
    'лето', 
    'индивидуальная, lookbook', 
    true, 
    44
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit44/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 45: Old money', 
    'Прекрасный женское образ для love-story и lookbook и семейная съёмка. Подходит на осень, весна.', 
    'женское', 
    'красный, черный', 
    'old money', 
    'осень, весна', 
    'love-story, lookbook, семейная съёмка', 
    true, 
    45
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit45/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 46: Романтика, классика', 
    'Прекрасный мужское образ для контент для соцсетей. Подходит на осень.', 
    'мужское', 
    'синий, черный', 
    'романтика, классика', 
    'осень', 
    'контент для соцсетей', 
    true, 
    46
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit46/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 47: Минимализм', 
    'Прекрасный женское образ для индивидуальная и семейная съёмка. Подходит на весна.', 
    'женское', 
    'бежевый, черный', 
    'минимализм', 
    'весна', 
    'индивидуальная, семейная съёмка', 
    true, 
    47
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit47/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 48: Old money', 
    'Прекрасный мужское образ для индивидуальная. Подходит на весна, осень.', 
    'мужское', 
    'черный', 
    'old money', 
    'весна, осень', 
    'индивидуальная', 
    true, 
    48
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit48/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 49: Casual, минимализм', 
    'Прекрасный мужское образ для беременность и love-story и контент для соцсетей. Подходит на зима.', 
    'мужское', 
    'белый', 
    'casual, минимализм', 
    'зима', 
    'беременность, love-story, контент для соцсетей', 
    true, 
    49
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit49/800/800', 0 FROM new_outfit;


WITH new_outfit AS (
  INSERT INTO public.outfits (title, description, gender, colors, styles, seasons, occasions, is_published, sort_order)
  VALUES (
    'Образ 50: Минимализм, романтика', 
    'Прекрасный мужское образ для индивидуальная. Подходит на осень, весна.', 
    'мужское', 
    'синий, серый', 
    'минимализм, романтика', 
    'осень, весна', 
    'индивидуальная', 
    true, 
    50
  )
  RETURNING id
)
INSERT INTO public.outfit_images (outfit_id, storage_path, sort_order)
SELECT id, 'https://picsum.photos/seed/outfit50/800/800', 0 FROM new_outfit;
