"""Content relevance checker for education-related articles"""
import re
from typing import Dict, Optional
from loguru import logger


class RelevanceChecker:
    """Check if article content is relevant to education and students"""

    # Ключевые слова, которые должны присутствовать (релевантные)
    RELEVANT_KEYWORDS = {
        'ru': [
            # Образование
            'образование', 'обучение', 'учеба', 'учёба', 'образовательный',
            'университет', 'вуз', 'институт', 'колледж', 'школа',
            'магистратура', 'бакалавриат', 'докторантура', 'аспирантура',

            # Студенты и выпускники
            'студент', 'студенты', 'студенческий',
            'выпускник', 'выпускники', 'выпускной',
            'абитуриент', 'абитуриенты',
            'школьник', 'школьники',

            # Гранты и стипендии
            'грант', 'гранты', 'грантовый',
            'стипендия', 'стипендии', 'стипендиат',
            'scholarship', 'fellowships', 'fellowship',
            'финансирование', 'финансирован',

            # Стажировки и программы
            'стажировка', 'стажировки', 'стажёр',
            'интернship', 'internship', 'intern',
            'программа обмена', 'обмен студентами',
            'волонтерство', 'волонтёр',

            # Обучение за рубежом
            'за рубежом', 'за границей', 'зарубеж',
            'международный', 'иностранный',
            'study abroad', 'обучение за рубежом',

            # Поступление и подача документов
            'поступление', 'поступить', 'поступающий',
            'подача документов', 'заявка', 'заявки',
            'дедлайн', 'deadline',
            'требования', 'admission',

            # Экзамены и тесты
            'ielts', 'toefl', 'sat', 'gmat', 'gre',
            'экзамен', 'экзамены', 'тест', 'тесты',
            'язык', 'языковой',

            # Курсы и обучение
            'курс', 'курсы', 'онлайн-курс',
            'тренинг', 'семинар', 'вебинар',
            'сертификат', 'сертификация',

            # Карьера и трудоустройство
            'карьера', 'карьерный',
            'трудоустройство', 'работа для студентов',
            'молодой специалист',
        ],
        'en': [
            # Education
            'education', 'educational', 'study', 'studying', 'learning',
            'university', 'college', 'institute', 'school',
            'master', 'bachelor', 'phd', 'doctorate', 'undergraduate', 'graduate',

            # Students
            'student', 'students', 'graduate', 'graduates',
            'applicant', 'applicants', 'pupil', 'pupils',

            # Scholarships and grants
            'scholarship', 'scholarships', 'grant', 'grants',
            'fellowship', 'fellowships', 'funding', 'funded',
            'financial aid', 'tuition',

            # Internships
            'internship', 'internships', 'intern', 'interns',
            'traineeship', 'trainee', 'placement',
            'exchange program', 'student exchange',

            # Study abroad
            'study abroad', 'abroad', 'international',
            'overseas', 'foreign',

            # Admission
            'admission', 'admissions', 'apply', 'application',
            'deadline', 'requirements', 'eligibility',

            # Tests
            'ielts', 'toefl', 'sat', 'gmat', 'gre',
            'test', 'exam', 'examination',

            # Courses
            'course', 'courses', 'online course',
            'training', 'seminar', 'webinar',
            'certificate', 'certification',

            # Career
            'career', 'job', 'employment',
            'young professional',
        ]
    }

    # Слова-исключения (нерелевантные темы)
    IRRELEVANT_KEYWORDS = {
        'ru': [
            # Политика
            'выборы', 'парламент', 'депутат', 'политик',
            'президент', 'правительство', 'министр',

            # Криминал
            'преступление', 'убийство', 'кража', 'арест',
            'суд', 'приговор', 'тюрьма',

            # Спорт (если не образовательный контекст)
            'футбол', 'хоккей', 'баскетбол',
            'чемпионат', 'олимпиада',

            # Развлечения
            'кино', 'фильм', 'актер', 'актриса',
            'концерт', 'шоу', 'сериал',

            # Бизнес (общий)
            'акции', 'биржа', 'инвестиции',
            'недвижимость', 'продажи',
        ],
        'en': [
            # Politics
            'election', 'parliament', 'politician',
            'president', 'government', 'minister',

            # Crime
            'crime', 'murder', 'theft', 'arrest',
            'court', 'sentence', 'prison',

            # Sports
            'football', 'soccer', 'basketball',
            'championship', 'olympics',

            # Entertainment
            'movie', 'film', 'actor', 'actress',
            'concert', 'show', 'series',

            # Business (general)
            'stock', 'shares', 'investment',
            'real estate', 'sales',
        ]
    }

    # Минимальное количество совпадений для релевантности
    MIN_RELEVANT_MATCHES = 1  # Снижено с 2 до 1 для меньших false negatives
    MAX_IRRELEVANT_MATCHES = 3  # Увеличено с 2 до 3 для контекстных исключений

    def __init__(self):
        self.relevant_patterns_ru = self._compile_patterns(self.RELEVANT_KEYWORDS['ru'])
        self.relevant_patterns_en = self._compile_patterns(self.RELEVANT_KEYWORDS['en'])
        self.irrelevant_patterns_ru = self._compile_patterns(self.IRRELEVANT_KEYWORDS['ru'])
        self.irrelevant_patterns_en = self._compile_patterns(self.IRRELEVANT_KEYWORDS['en'])

    def _compile_patterns(self, keywords: list) -> list:
        """Compile regex patterns from keywords with word variations"""
        patterns = []
        for keyword in keywords:
            # For Russian words, add flexibility for different endings
            # For example: университет -> университет[а-я]{0,3}
            if any(ord(c) >= 1040 and ord(c) <= 1103 for c in keyword):  # Cyrillic
                # Allow 0-3 characters after the root for declensions
                pattern = re.compile(
                    r'\b' + re.escape(keyword.lower()) + r'[а-яё]{0,3}\b',
                    re.IGNORECASE | re.UNICODE
                )
            else:
                # For English, match exact word + common endings (s, ed, ing)
                pattern = re.compile(
                    r'\b' + re.escape(keyword.lower()) + r'(s|ed|ing)?\b',
                    re.IGNORECASE
                )
            patterns.append((keyword, pattern))
        return patterns

    def check_relevance(self, title: str, content: str = "") -> Dict:
        """
        Check if article is relevant to education topic

        Returns:
            {
                'is_relevant': bool,
                'score': float (0-1),
                'relevant_matches': list,
                'irrelevant_matches': list,
                'reason': str
            }
        """
        text = f"{title} {content}".lower()

        # Count relevant matches
        relevant_matches = []
        for keyword, pattern in self.relevant_patterns_ru + self.relevant_patterns_en:
            if pattern.search(text):
                relevant_matches.append(keyword)

        # Count irrelevant matches
        irrelevant_matches = []
        for keyword, pattern in self.irrelevant_patterns_ru + self.irrelevant_patterns_en:
            if pattern.search(text):
                irrelevant_matches.append(keyword)

        # Calculate score
        relevant_count = len(relevant_matches)
        irrelevant_count = len(irrelevant_matches)

        # Determine relevance
        is_relevant = False
        reason = ""

        # If there are relevant matches, check if irrelevant matches should disqualify
        if relevant_count >= self.MIN_RELEVANT_MATCHES:
            # If we have relevant matches, only disqualify if irrelevant >> relevant
            if irrelevant_count > self.MAX_IRRELEVANT_MATCHES and irrelevant_count > relevant_count * 2:
                reason = f"Слишком много нерелевантных слов ({irrelevant_count} vs {relevant_count} релевантных)"
            else:
                is_relevant = True
                if irrelevant_count > 0:
                    reason = f"Найдено {relevant_count} релевантных слов (игнорируем {irrelevant_count} контекстных)"
                else:
                    reason = f"Найдено {relevant_count} релевантных слов"
        else:
            reason = f"Недостаточно релевантных слов ({relevant_count} < {self.MIN_RELEVANT_MATCHES})"

        # Calculate score (0-1)
        score = min(1.0, relevant_count / (self.MIN_RELEVANT_MATCHES * 2))
        if irrelevant_count > 0:
            score = max(0, score - (irrelevant_count * 0.2))

        result = {
            'is_relevant': is_relevant,
            'score': round(score, 2),
            'relevant_matches': relevant_matches[:5],  # Top 5
            'irrelevant_matches': irrelevant_matches[:3],  # Top 3
            'reason': reason
        }

        logger.debug(
            f"Relevance check: {is_relevant} (score: {score:.2f})\n"
            f"Title: {title[:50]}...\n"
            f"Relevant: {relevant_matches[:3]}\n"
            f"Irrelevant: {irrelevant_matches[:3]}"
        )

        return result

    def is_relevant(self, title: str, content: str = "") -> bool:
        """Quick check if content is relevant"""
        result = self.check_relevance(title, content)
        return result['is_relevant']


# Global instance
relevance_checker = RelevanceChecker()
