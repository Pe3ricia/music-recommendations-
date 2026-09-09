# Выбор промпта для базы музыкальных описаний

## Итог

Лучший результат **`p1_structured_closure`**.

Причина: p1 чаще остальных даёт связное описание по делу, благодаря чётко заданной структуре ответа. Он последовательно говорит:

1. какое у трека настроение;
2. к какому стилю он ближе;
3. какой у него ритм и энергия;
4. что звучит и есть ли вокал.

Остальные промпты иногда дают удачные фразы, но в среднем чаще добавляют похожие друг на друга шаблоны.

---

## Что тестировалось

Для каждого трека были сгенерированы пять описаний:

| Промпт | Задача |
|---|---|
| `p1_structured_closure` | Структурированное описание: настроение, стиль, ритм, инструменты, вокал |
| `p2_emotion_forward` | Описание через эмоции |
| `p3_sonic_detail` | Акцент на звуках, темпе, инструментах и деталях |
| `p4_user_query_style` | Описание как свободный поисковый запрос |
| `p5_scene_imagery` | Описание через сцену или воображаемый контекст |

Оценка проводилась преимущественно вручную 

"p1_structured_closure": (
        "You are an expert music critic. Listen carefully to the audio track and write exactly one "
        "coherent paragraph describing the music. In 4-5 sentences, cover in order: (1) atmosphere and mood, "
        "(2) general style or genre direction in natural language, (3) energy, and (4) dominant "
        "instruments or sounds and (5) vocals if present. Use clear, concrete language, not vague praise. "
        "Do not use labels, lists, metadata, code, or technical terms."
    ),

    "p2_emotion_forward": (
        "Listen to the audio track and describe it primarily through the emotions it creates. "
        "Write 3-5 sentences that focus first on atmosphere, emotional color, and how the track would feel "
        "to a listener, then briefly mention the most important sonic elements like rhythm, instrumentation, "
        "and vocals if present. Use expressive but honest language. Do not output labels, tags, lists, "
        "metadata, or any technical wording."
    ),

    "p3_sonic_detail": (
        "Listen to the track and write a concise, factual description that emphasizes what can be heard. "
        "Describe in 3-5 sentences the mood, style, tempo or groove, and the main instruments, sound layers, "
        "and vocal characteristics if present. Use concrete sensory details and avoid figurative or overly "
        "poetic language. Do not use labels, lists, metadata fields, parameters, or code-like text."
    ),

    "p4_user_query_style": (
        "Imagine a listener trying to describe this track in a text search box. Listen to the music and "
        "write 3-5 natural sentences in the style of such a free-form query, mentioning mood, style, "
        " or movement and vocals. Use everyday language that a non-expert might use, "
        "avoiding jargon. Do not output labels, tags, lists, metadata, or technical terms."
    ),

    "p5_scene_imagery": (
        "Listen to the audio track and describe it by painting a small scene that matches the music, "
        "then anchor that scene in real sonic details. In 3-5 sentences, start from the atmosphere and "
        "imagined setting, then clearly mention the rhythm, main instruments or sound textures, and vocals "
        "if present. Keep the description evocative but tied to what is actually heard. "
        "Do not use labels, lists, metadata fields, or technical language."
    ),

---

## Почему выбран p1

### Стабильная структура

P1 чаще остальных проходит по ключевым признакам трека. Это делает тексты сопоставимыми между собой и полезными для семантического поиска.

Пример для `000787.mp3`:

> “the track features a slow tempo and a focus on atmosphere and mood, with a general style or genre direction that leans towards experimental or avant-garde music. the rhythm is steady and consistent, with a moderate energy level that supports the overall mood. the dominant instruments are the piano and vocals…”

В одном коротком тексте есть:

- медленный темп и атмосферность;
- экспериментальный/авангардный стиль;
- ровный ритм и умеренная энергия;
- пианино и вокал.

Это уже хороший набор слов для связей с запросами вроде: «медленная экспериментальная музыка с пианино», «спокойный атмосферный трек с вокалом».

Пример для более тяжёлого `000452.mp3`:

> “the track features a dense, atmospheric soundscape… the general style is characterized by its experimental and avant-garde approach… the rhythm is energetic and driving… the dominant instruments are distorted guitars and synthesizers… the vocals are absent…”

Текст даёт достаточно конкретные ориентиры: плотный звук, драйв, искажённые гитары, синтезаторы, отсутствие вокала.

### Меньше бессодержательной генерации

P1 тоже бывает шаблонным: часто встречаются обороты вроде `the track features`, `steady and consistent`, `focus on atmosphere`. Но ответ всё равно всегда содержит подробности: он называет характер, стиль, ритм и звуки.

Например, для `001499.mp3` p1 выдаёт спокойное и цельное описание:

> “the track features a slow tempo and a spacious, ambient soundscape, creating a sense of calm and introspection. the general style or genre direction is electronic… the dominant instruments are synthesizers and electronic effects…”

Для семантической базы это важны именно уникальные подробности.

---

## Проблемы генерации

### 1. У одного трека разные промпты называют АБСОЛЮТНО разные BPM, тажке путает тональности

Описание не должно содеражить BPM и тональности.

#### Пример: `000780.mp3`

| Промпт | Что сказано о темпе |
|---|---|
| p1 | `slow tempo`, умеренная энергия |
| p2 | `slow tempo` |
| p3 | `slow tempo, around 70 bpm` |
| p4 | `tempo of 176.5 bpm` |
| p5 | не даёт число, но описывает напряжённый пульс и движение |

70 BPM и 176.5 BPM — это не небольшая погрешность, а совершенно разные представления о треке. 

#### Пример: `000452.mp3`

| Промпт | Что сказано о темпе |
|---|---|
| p1 | нет точного BPM; энергичный, драйвовый ритм |
| p3 | `fast tempo` |
| p4 | `around 176 bpm` |
| p5 | `around 110 bpm` |

176 BPM и 110 BPM — слишком большая разница, чтобы считать эти числа надёжными.

#### Пример: `000787.mp3`

| Промпт | Что сказано о темпе |
|---|---|
| p1 | `slow tempo` |
| p2 | `slow tempo` |
| p3 | `around 90 bpm` |
| p4 | `upbeat tempo` |
| p5 | `tempo of 115 bpm` |

Почти всегда модели расходятся: p3 пишет около 90 BPM, p5 — 115 BPM, p4 вообще называет темп бодрым (`upbeat`).

**Вывод:** точные BPM, размер и тональность из текстовой генерации нельзя сохранять как метаданные трека. Если эти признаки нужны, их надо получать отдельным аудио-анализатором.

---


### 2. P2–P5 чаще производят похожую друг на друга дичь

Повторяющиеся, слабо проверяемые и часто не связанные с конкретным треком конструкции: одни и те же эмоции, типовые футуристические сцены, постоянные `driving rhythm`, `ambient textures` и `sparse vocals`.

#### P2: одинаковые эмоциональные клише

P2 очень часто использует похожий словарь:

- `serene and introspective atmosphere`;
- `haunting and introspective atmosphere`;
- `sense of urgency and tension`;
- `emotional depth`;
- `if present, would likely…`.

Например, для `000787.mp3`:

> “the track creates a serene and introspective atmosphere, with a touch of melancholy…”

Для `001499.mp3`:

> “the track creates a serene and introspective atmosphere, with a sense of calm and contemplation…”

Для `000418.mp3`:

> “the track creates a haunting and introspective atmosphere, with a sense of mystery and exploration…”

Такие слова сами по себе полезны, но при массовой генерации они становятся шаблоном: слишком многие треки превращаются в «интроспективные», «загадочные» и «эмоционально глубокие».

У p2 также есть прямой повтор в описании `000548.mp3`: блок о редком «haunting» вокале и минимальной инструментовке повторён два раза подряд. Это явный артефакт генерации.

#### P3: одинаковая псевдофактическая формула

P3 часто повторяет примерно один и тот же шаблон для электроники:

> “fast tempo and a steady, driving rhythm, with a prominent electronic beat and synthesized sounds…”

Он появляется, например, для `000955.mp3` и `000315.mp3`; похожая формула используется для `000791.mp3`. Вместо различения треков модель подставляет универсальный образ энергичной электронной музыки.

Проблема усиливается тем, что к этому шаблону добавляются конкретные, но непроверенные BPM и размеры.

#### P4: одинаковые технические выдумки

Вместо полезного «живого» языка p4 регулярно вставляет одну и ту же техническую конструкцию. 

#### P5: похожие сцены и лишние образы

P5 повторяет сценарные клише:

- `bustling city street`;
- `futuristic, otherworldly atmosphere`;
- `dystopian or post-apocalyptic setting`;
- `sunny day at the beach`;
- `perfect for meditation, relaxation, or contemplation`.

Например:

- `000452.mp3` — «dystopian or post-apocalyptic setting»;
- `000780.mp3` — «modern, urban setting»;
- `000791.mp3` — «suitable for a sci-fi movie or video game»;
- `001174.mp3` — «sunny day at the beach».

Сцены могут быть красивыми, но для основной базы они часто дают больше интерпретации, чем информации о музыке. Два разных трека могут получить один и тот же типовой образ «футуристического города» просто потому, что модель услышала синтезаторы и ритм.

---

## Вывод

Для генерации основной базы использовать p1, но  обновить формулировку:

- сохранить его строгий порядок: настроение → стиль → ритм → звуки → вокал;
- попросить более простой и живой язык;
- запретить BPM, тональность, размер и другие точные технические параметры;
- запретить пустые оценки вроде `captivating`, `immersive`, `powerful` без конкретного объяснения;
- сохранить один связный абзац на 4–5 предложений.

Рабочая версия:

```python
"p1_structured_closure_v2": (
    "You are a listener trying to describe this track. Listen to the audio track "
    "and write one coherent paragraph"
    "In 5 natural sentences, cover in order: (1) atmosphere and mood"
    "(2) general style or genre direction in simple, everyday words"
    "(3) energy"
    "(4) dominant instruments or sound textures, and (5) vocals if present and how they come across. "
    "Use varied, natural wording"
    "Do not invent exact technical values like BPM, key, or time signature, and do not use labels, lists, "
    "metadata fields, code-like text, or specialized technical terms."
)
```

## Финальный вывод

P1 выбран не потому, что он идеален, а потому, что среди проверенных вариантов он наиболее предсказуем и менее склонен к бессмысленным добавлениям.

Его тексты содержат полезные для поиска слова о стиле, настроении, энергии, инструментах и вокале. P2–P5 чаще добавляют похожие друг на друга клише, художественные сцены или выдуманную техническую информацию. Поэтому разумная стратегия — развивать p1, а не строить основную базу на более «живых», но менее надёжных вариантах.
