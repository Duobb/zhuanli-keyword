import os
import pdfplumber
import re

def parse_pdf_dynamic(filepath):
    results = []
    current_chapter = ""
    
    with pdfplumber.open(filepath) as pdf:
        last_context = ""
        global_ipc_x_min = 160
        global_kw_x_min = 380
        
        for i, page in enumerate(pdf.pages):
            words = page.extract_words()
            if not words:
                continue
                
            # Find chapter title
            for w in words:
                text = w['text'].strip()
                if re.match(r'^（[一二三四五六七八九十]+）.*分类体系表$', text):
                    current_chapter = text
                    
            page_ipc_min = None
            page_kw_min = None
            
            # dynamic find
            for w in words:
                if "国际专利" in w['text'] and w['top'] < 300:
                    page_ipc_min = float(w['x0']) - 80 
                if ("关键词" in w['text'] or "参考关键" in w['text']) and w['top'] < 300:
                    v_edges = [e for e in page.edges if e['height'] > 50 and (e['x1'] - e['x0']) < 5]
                    v_tops = sorted(list(set([e['x0'] for e in v_edges])))
                    candidates = [x for x in v_tops if w['x0'] - 150 < x < w['x0'] + 30]
                    if candidates:
                        page_kw_min = max(candidates)
                    else:
                        page_kw_min = float(w['x0']) - 50
                    
            if page_ipc_min is not None:
                if page_ipc_min < 50: page_ipc_min = 160
                global_ipc_x_min = page_ipc_min
                
            if page_kw_min is not None:
                if page_kw_min < 200: page_kw_min = 380
                global_kw_x_min = page_kw_min
                
            ipc_x_min = global_ipc_x_min
            kw_x_min = global_kw_x_min
            
            edges = [e for e in page.edges if e['width'] > 50 and (e['y1'] - e['y0']) < 5]
            tops = sorted(list(set([e['top'] for e in edges])))
            
            filtered_tops = []
            for t in tops:
                if not filtered_tops or t - filtered_tops[-1] > 2:
                    filtered_tops.append(t)
                    
            if len(filtered_tops) < 2:
                # No clear horizontal lines. Fallback: line-by-line soft grouping
                # Sort chars by top
                chars_sorted = sorted(page.chars, key=lambda c: c['top'])
                # Just group by simple y threshold (e.g. 5 points)
                current_y = None
                row_chars = []
                for c in chars_sorted:
                    if current_y is None or abs(c['top'] - current_y) < 5:
                        row_chars.append(c)
                        current_y = c['top']
                    else:
                        _process_row_chars(row_chars, ipc_x_min, kw_x_min, results, filepath, i+1, current_chapter)
                        row_chars = [c]
                        current_y = c['top']
                _process_row_chars(row_chars, ipc_x_min, kw_x_min, results, filepath, i+1, current_chapter)
                continue
                
            # We have table rows bounded by filtered_tops
            for j in range(len(filtered_tops) - 1):
                top = filtered_tops[j]
                bottom = filtered_tops[j+1]
                
                row_chars = [c for c in page.chars if c['bottom'] > top and c['top'] < bottom]
                if not row_chars:
                    continue
                    
                _process_row_chars(row_chars, ipc_x_min, kw_x_min, results, filepath, i+1, current_chapter)

    # Post processing forward-fill context
    stack = {} # key: depth, value: text
    stack[0] = ""
    
    filled_results = []
    
    for r in results:
        chap = r.get('chapter', '')
        ctx = r['context_text']
        ipc = r['ipc_text']
        kw = r['keywords_text']
        
        ctx_clean = ctx.replace('\n', '')
        
        # Determine depth
        depth = -1
        m = re.match(r'^(\d+(?:\.\d+)*)\s*(.*)', ctx_clean)
        num_str = ""
        if m:
            num_str = m.group(1)
            depth = len(num_str.split('.'))
        
        if depth != -1:
            stack[depth] = ctx_clean
            # Clear deeper levels
            for k in list(stack.keys()):
                if k > depth:
                    del stack[k]
        
        # Build full ctx
        full_ctx_parts = []
        if chap: full_ctx_parts.append(chap)
        for d in range(1, max(stack.keys()) + 1 if stack else 1):
            if d in stack:
                full_ctx_parts.append(stack[d])
        
        if depth == -1 and ctx_clean:
            # Maybe a continuation or something without numbers? Just append.
            full_ctx_parts.append(ctx_clean)
            
        full_ctx = "-".join(full_ctx_parts)
            
        # We only keep rows that have IPC codes
        if any(char.isdigit() for char in ipc) and any(char.isalpha() for char in ipc):
            # A valid IPC usually has letters and numbers
            filled_results.append({
                'source': r.get('source', ''),
                'page': r.get('page', ''),
                'context_text': full_ctx,
                'ipc_text': ipc,
                'keywords_text': kw
            })

    return filled_results
    
def _process_row_chars(row_chars, ipc_x_min, kw_x_min, results, filepath, page_num, chapter):
    # For a row, we want to group characters into ctx, ipc, kw.
    # Since text can be multiple lines within the cell, we should sort by top, then x0
    row_chars.sort(key=lambda c: (round(c['top'] / 4) * 4, c['x0']))
    
    ctx_text = ""
    ipc_text = ""
    kw_text = ""
    
    for c in row_chars:
        x0 = c['x0']
        char_text = c['text']
        if x0 < ipc_x_min:
            ctx_text += char_text
        elif ipc_x_min <= x0 < kw_x_min:
            ipc_text += char_text
        else:
            kw_text += char_text
            
    ctx_str = ctx_text.strip()
    ipc_str = ipc_text.strip()
    kw_str = kw_text.strip()
    
    if "国际专利" in ipc_str or "关键词" in kw_str or "分支" in ctx_str:
        return
        
    results.append({
        'chapter': chapter,
        'source': os.path.basename(filepath),
        'page': page_num,
        'context_text': ctx_str,
        'ipc_text': ipc_str,
        'keywords_text': kw_str
    })


def parse_document(filepath):
    """
    Entry point for parsing a document.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        try:
            return parse_pdf_dynamic(filepath)
        except Exception as e:
            print(f"Error parse_pdf_dynamic: {e}")
            return []
    else:
        return []

