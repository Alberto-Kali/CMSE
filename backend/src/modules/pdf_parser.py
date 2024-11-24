import pdfplumber
import re

class PDFParser:
    def __init__(self, threshold_distance=20, header_height=7, sport_names_text_height=12,
                 sport_compositions_names=None):
        """
        Инициализация парсера PDF.

        :param pdf_path: Путь к PDF файлу для парсинга.
        :param threshold_distance: Минимальное расстояние между словами для их разделения (по умолчанию 20).
        :param header_height: Количество строк заголовка для пропуска (по умолчанию 7).
        :param sport_names_text_height: Высота текста названий видов спорта (по умолчанию 12).
        :param sport_compositions_names: Список названий составов спорта для поиска (по умолчанию ["Основной состав", "Молодежный (резервный) состав"]).
        """
        self.threshold_distance = threshold_distance
        self.header_height = header_height
        self.sport_names_text_height = sport_names_text_height
        self.sport_compositions_names = sport_compositions_names or ["Основной состав", "Молодежный (резервный) состав"]

    def parse(self, pdf_path):
        """
        Парсит PDF файл и извлекает информацию о спортивных соревнованиях.

        :return: Список кортежей, содержащих извлеченную информацию о соревнованиях.
        """
        with pdfplumber.open(pdf_path) as pdf:
            final_string = ""
            sport_composition = "default"
            sport_name = "default"
            sport_names = []
            final_mas = []
            
            for ind, page in enumerate(pdf.pages[0:50]):  # Обработка первых 50 страниц
                words = page.extract_words()
                processed_lines = []
                current_line = []
                
                for i in range(len(words)):
                    current_word = words[i]['text']
                    current_line.append(current_word)
                    if int(words[i]['height']) == self.sport_names_text_height:
                        spn = ""
                        spn += words[i]['text']
                        for j in range(1, 9):
                            if (i + j < len(words) and int(words[i + j]['height']) == self.sport_names_text_height and
                                    int(words[i - j]['height']) != self.sport_names_text_height):
                                spn += " " + words[i + j]['text']
                            else:
                                if int(words[i - j]['height']) != self.sport_names_text_height:
                                    sport_names.append(spn)
                                break
                    
                    if i < len(words) - 1:
                        distance = words[i + 1]['x0'] - words[i]['x1']
                        if distance > self.threshold_distance:
                            current_line.append('|')
                    
                    if i == len(words) - 1 or words[i]['top'] != words[i + 1]['top']:
                        processed_line = ' '.join(current_line)
                        processed_lines.append(processed_line)
                        current_line = []
                
                if ind == 0:
                    processed_lines = processed_lines[self.header_height:]

                for line in processed_lines:
                    if "Стр." in line:
                        continue
                    
                    line = line.strip()

                    if line == line.upper() and "|" not in line and line.strip() in sport_names:
                        sport_name = line
                        continue
                    
                    if line in self.sport_compositions_names:
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
                date_end = new [6].strip()
                city = new[7].strip()
                discipline = " ".join([" ".join(x.strip().split("|")) for x in new[8:-2]])
                sport_name = new[-2].strip()
                sport_composition = new[-1].strip()
            except Exception as e:
                print("skip", e)
                continue
            
            final_mas.append((sport_name, sport_composition, ekp_number, date_start, date_end, city, discipline, competition_class, country, max_people_count, genders_and_ages))  # Вывод нужной информации
        
        return final_mas