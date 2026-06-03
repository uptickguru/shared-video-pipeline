import re

def sync_content_file():
    content_path = "content.py"
    with open(content_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Food safety mappings
    food_safety_replacements = {
        '{"prompt": "A cinematic extreme close-up of a digital meat thermometer being inserted into a thick, steaming grilled steak. The red digital numbers rapidly climb to 165. macro lens, highly detailed.",':
        '{"prompt": "An extreme macro, high-speed cinema shot of a glowing digital meat thermometer piercing into a succulent, sizzling, thick-cut grilled ribeye steak. Volumetric steam swirls and rich meat juices bubble dynamically under moody, warm dramatic restaurant kitchen lighting. Anamorphic lens flare, 4k resolution, cinematic masterpiece.",',
        
        '{"prompt": "A pristine, stainless-steel commercial kitchen. A chef in a crisp white uniform meticulously washes their hands with steaming hot water and antibacterial soap. cinematic lighting, 4k.",':
        '{"prompt": "A slow-motion cinematic tracking shot of a professional chef in a crisp white uniform washing hands in a clean, gleaming stainless-steel commercial sink. Steaming hot water splashes vigorously, soap bubbles lathering in rich, high-detail macro close-ups, shot on Arri Alexa with deep volumetric warm lights.",',
        
        '{"prompt": "A time-lapse of a massive industrial walk-in refrigerator. Neatly labeled and dated plastic bins of prepped vegetables are stacked on pristine wire racks. cold blue lighting.",':
        '{"prompt": "A slow, elegant dolly-in camera sweep through a massive, cold, industrial walk-in refrigerator. Volumetric blue fog drifts past neatly stacked rows of glowing green and red fresh prepped vegetable bins on wire racks. Cinematic atmosphere, sharp focus, 4k.",',
        
        '{"prompt": "An extreme macro shot of a cutting board. On the left side, raw chicken is being chopped. The right side is glowing with microscopic bacteria spreading. hyper-realistic, medical visualization style.",':
        '{"prompt": "A jaw-dropping, high-contrast creative visual transition. The camera macro-dives into a wooden cutting board where raw chicken is chopped. The lens shifts to a highly detailed, surreal sci-fi microscopic view: glowing neon-green bacteria cells dynamically multiplying and spreading in slow motion across the screen. Cinematic, rich depth of field.",',
        
        '{"prompt": "A chef wearing black nitrile gloves carefully uses a sanitizing wipe to clean a stainless steel prep station until it gleams. highly detailed, cinematic.",':
        '{"prompt": "A cinematic low-angle glide following a chef wearing black nitrile gloves carefully wiping down a gleaming stainless steel prep counter with a sanitizing rag. Bright overhead lights create a beautiful starburst reflection along the polished steel surface as a fine mist of sanitizer spray floats in the air.",',
        
        '{"prompt": "A glowing digital temperature gauge on the outside of a commercial proofing cabinet displaying exactly 100 degrees Fahrenheit. Steam slightly fogs the glass. cinematic lighting.",':
        '{"prompt": "A slow, moody camera pan across the steaming glass door of an industrial proofing cabinet. A glowing digital temperature gauge displays exactly 100 degrees Fahrenheit through thick swirling condensation that drips slowly down the glass. Volumetric warm golden interior glow.",',
        
        '{"prompt": "A health inspector in a suit holding a clipboard, standing in a busy commercial kitchen, shining a bright flashlight into a dark corner. dramatic lighting, tense atmosphere.",':
        '{"prompt": "A tense, dramatic cinematic shot of a health inspector in a dark suit standing in a busy commercial kitchen. A powerful handheld flashlight beam cuts through the volumetric haze and shadows, scanning dark corners in a slow-pan sweep. Moody, high-contrast noir lighting.",',
        
        '{"prompt": "A cinematic shot of a massive industrial dishwasher blasting plates with high-pressure, steaming hot water. The plates emerge sparkling clean. dynamic lighting, 4k.",':
        '{"prompt": "A high-action, dynamic camera dive inside a massive industrial dishwasher. Jets of high-pressure, steaming hot water blast plates and glasses in slow motion, creating spectacular splashing, water droplets, and swirling steam. Bright, intense under-water lighting, cinematic.",',
        
        '{"prompt": "A chef urgently grabbing a fire extinguisher off the wall as a massive grease fire erupts on a commercial stove. intense lighting, fast shutter speed, high action.",':
        '{"prompt": "An intense, high-action slow-motion cinema shot. A massive grease fire erupts dynamically on a commercial stove with bright orange and yellow flames roaring upwards. A chef in extreme close-up grabs a red fire extinguisher as volumetric smoke swirls through the frame. Highly dramatic, fast camera shake.",',
        
        '{"prompt": "A beautiful, perfectly plated gourmet dish being set down on a white tablecloth in a high-end restaurant. The lighting is warm and inviting. cinematic.",':
        '{"prompt": "A smooth, elegant tracking shot as a perfectly plated gourmet masterpiece is set down on a fine white tablecloth. A slow camera pan reveals steam gently rising from the dish while warm, inviting restaurant lighting reflects off polished silver cutlery. Breathtaking depth of field.",'
    }

    # Insurance mappings
    insurance_replacements = {
        '{"prompt": "A cinematic, dramatic wide shot of a massive, dark hurricane cloud formation looming over a vulnerable Florida coastal town. eerie lighting, storm brewing.",':
        '{"prompt": "A breathtaking, dark cinematic wide shot of a massive, swirling hurricane cloud vortex looming over a vulnerable Florida coastal town. Ominous blue-grey volumetric lighting, violent wind gusts bending palm trees in the foreground, creating a tense, apocalyptic storm atmosphere.",',
        
        '{"prompt": "A close-up of a distressed homeowner's hands tearing open a letter. The paper reads 'POLICY CANCELED' in bold red letters. highly detailed, dramatic shadows.",':
        '{"prompt": "A high-contrast macro shot of a distressed homeowner\'s hands tearing open an insurance cancellation letter in slow motion. The camera tracks closely as paper shreds, revealing \'POLICY CANCELED\' in bold red ink. Dramatic shadows and emotional lighting, shot on Arri Alexa.",',
        
        '{"prompt": "A hyper-realistic aerial shot of a neighborhood completely destroyed by a hurricane. Roofs are ripped off, but one house stands perfectly intact. 4k resolution.",':
        '{"prompt": "A breathtaking, high-altitude cinematic drone shot gliding slowly over a coastal neighborhood destroyed by a hurricane. The camera pans down to show splintered wood and debris, circling a single, beautifully intact modern house standing strong under a dramatic golden sun. Masterpiece.",',
        
        '{"prompt": "A sleek, modern corporate boardroom in a skyscraper overlooking New York City. Executives in expensive suits are laughing and shaking hands. cinematic, cold blue tint.",':
        '{"prompt": "A cold, high-contrast cinematic shot of a luxurious skyscraper boardroom overlooking New York City at night. Wealthy executives in expensive tailored suits stand in dark silhouettes against glowing city lights, laughing and clinking glasses. Moody volumetric shadows.",',
        
        '{"prompt": "A cinematic shot of a large blue tarp completely covering the roof of a Florida suburban home. Rain is pouring down heavily on it. gloomy, dramatic lighting.",':
        '{"prompt": "A dramatic close-up tracking shot of heavy rain pouring and splashing violently on a bright blue tarp covering the roof of a suburban home. Water droplets explode in slow motion under gloomy, volumetric storm clouds as palm trees sway aggressively in the background.",',
        
        '{"prompt": "A massive stack of complex legal documents and insurance contracts slamming down on a wooden desk. Dust flies up into the air. macro lens, slow motion.",':
        '{"prompt": "A spectacular slow-motion cinema shot of a massive stack of thick legal documents slamming down onto a mahogany desk. A cloud of volumetric dust particles erupts and floats through dramatic golden sunbeams cutting through the room. Macro lens, high action.",',
        
        '{"prompt": "An elderly couple sitting at a kitchen table, looking extremely stressed and exhausted while staring at an open laptop showing a massive bill. dramatic, emotional lighting.",':
        '{"prompt": "An emotional, high-contrast cinematic portrait of an elderly couple sitting at a dark kitchen table. The warm glow of a laptop screen illuminates their stressed, tearful faces as they stare at a massive billing statement. Soft volumetric shadows, deep emotional atmosphere.",',
        
        '{"prompt": "A fierce lawyer in a sharp suit slamming his fist on a table in a courtroom. The lighting is intense and focused. 4k, cinematic.",':
        '{"prompt": "An intense, dramatic wide shot of a fierce defense lawyer slamming his fist on a courtroom table in slow motion. Volumetric light shafts cut through the high-ceilinged room, illuminating floating dust and the lawyer\'s sharp suit. Tense, high-contrast masterpiece.",',
        
        '{"prompt": "A beautiful, sunny day on the Florida coast. A family is smiling and relaxing on their newly rebuilt porch. warm golden hour lighting, hopeful atmosphere.",':
        '{"prompt": "A warm, hopeful cinematic pan across a smiling family relaxing on the porch of their newly rebuilt coastal home. Golden hour sunlight bathes the scene in volumetric god rays as a soft sea breeze rustles the nearby palm trees. Breathtaking, emotional ending.",'
    }

    # DBAT mappings
    dbat_replacements = {
        '{"prompt": "A highly cinematic, ultra-modern creative agency office. Massive glass walls display glowing streams of digital data, websites, and SEO analytics. futuristic lighting, neon blue and purple.",':
        '{"prompt": "A highly cinematic, slow camera sweep through an ultra-modern creative agency office. Glowing neon-blue and purple lines of digital data and SEO metrics float as futuristic holograms in front of sleek glass walls. Volumetric cyberpunk lighting, highly detailed.",',
        
        '{"prompt": "A macro shot of a graphic designer's hand using a digital stylus on a glowing tablet, drawing a sleek, modern corporate logo. highly detailed, 4k.",':
        '{"prompt": "A macro-tracking shot of a designer\'s hand using a glowing digital stylus on an active tablet, drawing a sharp, minimalist corporate logo. Light glows from the screen, reflecting off the designer\'s skin under moody studio lighting, highly detailed, Arri Alexa.",',
        
        '{"prompt": "A fast-paced montage of a glowing server rack, lines of complex HTML code scrolling rapidly, and a beautiful modern website loading instantly on a smartphone. cyberpunk aesthetic.",':
        '{"prompt": "A fast-paced, high-action cyberpunk montage. The camera dives through glowing blue server racks, lines of neon-green HTML code scrolling rapidly in 3D space, transitioning to a gorgeous website loading instantly on a sleek modern smartphone. High speed, volumetric flares.",',
        
        '{"prompt": "A cinematic shot of a massive wall of monitors showing Google search rankings skyrocketing to the number one spot. The line graph glows bright green. volumetric lighting.",':
        '{"prompt": "A cinematic low-angle glide sweeping past a massive wall of glowing monitors displaying Google search metrics. A bright green line graph shoots rapidly upwards in a dynamic, smooth curve, reflecting off polished modern surfaces under volumetric overhead lights.",',
        
        '{"prompt": "A professional film crew on a high-end commercial set. A massive cinema camera on a robotic arm sweeps past a dramatic lighting setup. highly detailed, realistic.",':
        '{"prompt": "A breathtaking behind-the-scenes cinema shot of a professional film crew. A massive carbon-fiber camera on a robotic arm sweeps smoothly past the lens, framing a highly dramatic lighting setup with volumetric haze and bright stage spotlights. Masterpiece.",',
        
        '{"prompt": "A sleek smartphone displaying a highly addictive, fast-paced viral video. A thumbs-up icon pops out of the screen in 3D. bright, vibrant colors.",':
        '{"prompt": "A vibrant, high-contrast creative close-up. A sleek smartphone displays a highly dynamic, fast-paced video, and a glowing 3D \'thumbs up\' icon explodes out of the screen in slow motion amidst a shower of glowing digital particle sparks. Fun, energetic motion.",',
        
        '{"prompt": "A dark, intense war room where a team of marketing strategists are analyzing a massive glowing map of digital ad conversions. cinematic, dramatic shadows.",':
        '{"prompt": "A dark, intense war room where strategists analyze a massive glowing 3D holographic map of digital ad conversions pulsing in real-time. Volumetric light beams illuminate their focused faces under deep, dramatic shadows. High-stakes atmosphere.",',
        
        '{"prompt": "A cinematic macro shot of a sleek black business card with the words \'Death By A Thousand\' embossed in shining silver foil. moody lighting.",':
        '{"prompt": "A moody cinematic macro-tracking shot of a sleek matte-black business card with the words \'Death By A Thousand\' embossed in shining silver foil. The camera rotates slowly as warm, low-key lighting creates dynamic metallic reflections. Cinematic realism.",',
        
        '{"prompt": "A massive, futuristic digital billboard in Times Square displaying a stunningly beautiful advertisement. The crowd below stops and stares in awe. 8k resolution.",':
        '{"prompt": "A spectacular wide-angle tracking shot through Times Square at night. A futuristic, ultra-crisp digital billboard displays a stunning, highly artistic advertisement, drawing the eyes of a walking crowd that stops and stares in awe. Volumetric neon city haze.",',
        
        '{"prompt": "A sleek, cinematic logo reveal for \'Death By A Thousand LLC\'. The text forms out of digital smoke and shattering glass. highly dynamic, 4k.",':
        '{"prompt": "A spectacular, highly dynamic cinematic logo reveal for \'Death By A Thousand LLC\'. A sleek, dark logo forms out of slow-motion swirling dark volumetric smoke as a sheet of crystal glass shatters and explodes towards the camera in ultra-slow motion. Highly dynamic masterpiece.",'
    }

    # Execute all replacements in code
    master_replacements = {**food_safety_replacements, **insurance_replacements, **dbat_replacements}
    
    for old, new in master_replacements.items():
        # Handle simple literal replacement
        code = code.replace(old, new)
        # Handle slightly mutated spacing or escaped characters
        escaped_old = old.replace("'", "\\'")
        escaped_new = new.replace("'", "\\'")
        code = code.replace(escaped_old, escaped_new)

    with open(content_path, "w", encoding="utf-8") as f:
        f.write(code)
    print("[SYNC] Successfully synchronized content.py static lists with all juiced-up prompts!")

if __name__ == "__main__":
    sync_content_file()
