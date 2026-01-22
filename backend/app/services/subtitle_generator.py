from typing import List, Dict, Any

class SubtitleGenerator:
    def format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def generate_srt(
        self,
        ocr_results: List[Dict[str, Any]],
        frame_interval: float = 1.0,
        min_duration: float = 1.0,
        merge_threshold: float = 0.5
    ) -> str:
        if not ocr_results:
            return ""
        
        merged = self._merge_consecutive_results(ocr_results, merge_threshold)
        
        srt_lines = []
        for i, item in enumerate(merged, 1):
            start_time: float = item['timestamp']
            end_time = start_time + max(min_duration, frame_interval)
            
            start_str = self.format_timestamp(start_time)
            end_str = self.format_timestamp(end_time)
            
            srt_lines.append(str(i))
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(item['text'])
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    def _merge_consecutive_results(
        self,
        results: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        if not results:
            return []
        
        merged = []
        current_text: str = results[0]['text']
        current_timestamp: float = float(results[0]['timestamp'])
        
        for i in range(1, len(results)):
            current = results[i]
            prev = results[i - 1]
            current_ts: float = float(current['timestamp'])
            prev_ts: float = float(prev['timestamp'])
            
            if current_ts - prev_ts <= threshold:
                if current['text'] != prev['text']:
                    if current_text and current_text != current['text']:
                        current_text = f"{current_text} {current['text']}"
                    else:
                        current_text = current['text']
            else:
                merged.append({
                    'timestamp': current_timestamp,
                    'text': current_text.strip()
                })
                current_text = current['text']
                current_timestamp = current_ts
        
        if current_text:
            merged.append({
                'timestamp': current_timestamp,
                'text': current_text.strip()
            })
        
        return merged
