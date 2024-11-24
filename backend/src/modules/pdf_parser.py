import pdfplumber
import re

def parse_db(pdf_path, threshold_distance=20, header_height=7, sport_names_text_height=12, sport_compositions_names=["Основной состав", "Молодежный (резервный) состав"]):
    '''
        Parses a PDF file at the given `pdf_path` and extracts relevant information about sports competitions. The function processes the first 50 pages of the PDF, extracting sport names, sport compositions, and competition details. The extracted information is returned as a list of tuples, where each tuple contains the sport name, sport composition, EKP number, start date, end date, city, discipline, competition class, country, maximum number of people, and genders and ages.
            
            The function takes the following parameters:
            - `pdf_path`: the path to the PDF file to be parsed
            - `threshold_distance`: the minimum distance between words to consider them as separate (default is 20)
            - `header_height`: the number of header lines to skip (default is 7)
            - `sport_names_text_height`: the height of the sport names text (default is 12)
            - `sport_compositions_names`: a list of sport composition names to look for (default is ["Основной состав", "Молодежный (резервный) состав"])
            
        The function returns a list of tuples, where each tuple contains the extracted information for a single competition.
    '''
    with pdfplumber.open(pdf_path) as pdf:
        final_string = ""
        sport_composition = "default"
        sport_name = "default"
        sport_names = []
        final_mas = []
        
        for ind, page in enumerate(pdf.pages[0:50]):  # Обработка первых 17 страниц
            words = page.extract_words()
            processed_lines = []
            current_line = []
            
            for i in range(len(words)):
                current_word = words[i]['text']
                current_line.append(current_word)
                if int(words[i]['height']) == sport_names_text_height:
                    spn = ""
                    spn += words[i]['text']
                    for j in range(1,9):
                        if int(words[i+j]['height']) == sport_names_text_height and int(words[i-j]['height']) != sport_names_text_height:
                            spn += " " + words[i+j]['text']
                        else:
                            if int(words[i-j]['height']) != sport_names_text_height:
                                sport_names.append(spn)
                            break
                    
                
                if i < len(words) - 1:
                    distance = words[i+1]['x0'] - words[i]['x1']
                    if distance > threshold_distance:
                        current_line.append('|')
                
                if i == len(words) - 1 or words[i]['top'] != words[i+1]['top']:
                    processed_line = ' '.join(current_line)
                    processed_lines.append(processed_line)
                    current_line = []
            
            if ind == 0:
                processed_lines = processed_lines[header_height:]

            for line in processed_lines:
                if "Стр." in line:
                    continue
                
                line = line.strip()

                if line == line.upper() and "|" not in line and line.strip() in sport_names:
                    sport_name = line
                    continue
                
                if line in sport_compositions_names:
                    sport_composition = line
                    continue
                
                if sport_composition != "default" and sport_name != "default":
                    number_match = re.match(r'(\d{16})', line)
                    if number_match:
                        number = number_match.group(0)
                        final_string += f" | {sport_name} | {sport_composition}\n\n\n"
                        final_string += f" | {number} | {line[len(number):].strip()}\n"
                    else:
                        final_string += f" | {line}\n"
                        if line == processed_lines[-2]:
                            final_string += f" {sport_name} | {sport_composition} "

    for line in final_string.strip().split("\n\n\n"):
        try:
            new = line.strip()[1:].split("|")
            ekp_number = new[0].strip()
            competition_class = new[1].strip()
            date_start = new[2].strip()
            country = new[3].strip()
            max_people_count = new[4].strip()
            genders_and_ages = new[5].strip()
            date_end = new[6].strip()
            city = new[7].strip()
            discipline = " ".join([" ".join(x.strip().split("|")) for x in new[8:-2]])
            sport_name = new[-2].strip()
            sport_composition = new[-1].strip()
        except Exception as e:
            print("skip", e)
            continue
        
        final_mas.append((sport_name, sport_composition, ekp_number, date_start, date_end, city, discipline, competition_class, country, max_people_count, genders_and_ages))  # Вывод нужной информации
    
    return final_mas