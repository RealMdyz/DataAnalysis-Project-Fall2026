import re
from typing import List, Dict, Any
import pandas as pd

def clean_sentence_text(text: str) -> str:
    """پاک‌سازی اولیه متن بدون حذف بار معنایی کلمات."""
    if not isinstance(text, str):
        return ""
    # تبدیل فاصله‌های چندگانه و کاراکترهای نامتعارف خط جدید به یک فاصله
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_sentences(text: str) -> List[str]:
    """
    تقطیع استاندارد و مستقل از وابستگی خارجی متن به جملات.
    پشتیبانی از علامت‌های مرسوم پایان جمله (. ! ؟ ? \n)
    """
    if not text:
        return []
    # شکستن روی پایان جملات بدون نیاز به دانلود پکیج punkt
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_review_sentences(
    df: pd.DataFrame, 
    text_col: str = "text",
    min_words: int = 3
) -> pd.DataFrame:
    """
    تقطیع نقدها به سطح جمله با حفظ متادیتاها جهت استخراج جنبه‌ها.
    جملات خیلی کوتاه (کمتر از min_words) فیلتر می‌شوند.
    """
    records: List[Dict[str, Any]] = []
    
    # ستون‌های متادیتا که باید همراه هر جمله حفظ شوند
    cols_to_keep = [col for col in ["review_id", "parent_asin", "rating", "timestamp"] if col in df.columns]
    
    for _, row in df.iterrows():
        raw_text = row.get(text_col, "")
        cleaned = clean_sentence_text(raw_text)
        if not cleaned:
            continue
            
        sentences = split_into_sentences(cleaned)
        for idx, sentence in enumerate(sentences):
            words = sentence.split()
            if len(words) >= min_words:
                item = {col: row[col] for col in cols_to_keep}
                item["sentence_id"] = f"{row.get('review_id', 'rev')}_{idx}"
                item["sentence_text"] = sentence
                item["sentence_word_count"] = len(words)
                records.append(item)
                
    return pd.DataFrame(records)