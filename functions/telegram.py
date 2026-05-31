import json
import requests
import re
import os

def handler(event, context):
    if event.get('httpMethod') != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    body = json.loads(event.get('body', '{}'))
    token = os.environ.get('TELEGRAM_TOKEN', '7884631997:AAH02f-Zrp4IRCdFd04huvKhcKC83Igd93Y')
    fb_token = os.environ.get('FB_TOKEN', 'EAAGNO4a7r2wBRvOgH56TN4fRt4XcW1wHqZA23qrrgwVteWymj279i92ZCHtSIYaDvma6GU9EsDzHjsqL3NNu6ZB76J5IFYpSVbV8aWwirNTPToDtXAkNLDvUzUuoNmulywPGg979Lsw637DZCghJr2roIYyWzqs4inJvnvw4YL4e4JmCmhO5TNZA92Bh0KgZDZD')
    
    message = body.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')
    
    def send_message(msg):
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        payload = {'chat_id': chat_id, 'text': msg}
        try:
            requests.post(url, json=payload, timeout=10)
        except:
            pass
    
    if not chat_id:
        return {'statusCode': 200, 'body': 'OK'}
    
    if text == '/start':
        send_message('Gửi username Facebook (vd: zuck) hoặc URL hoặc UID để lấy thông tin công khai')
        return {'statusCode': 200, 'body': 'OK'}
    
    identifier = None
    id_type = None
    
    url_match = re.search(r'facebook\.com/([A-Za-z0-9.]+)', text)
    if url_match:
        identifier = url_match.group(1)
        id_type = 'username'
    else:
        user_match = re.search(r'^[A-Za-z][A-Za-z0-9.]{4,50}$', text)
        if user_match:
            identifier = user_match.group(0)
            id_type = 'username'
        else:
            uid_match = re.search(r'\b\d{10,20}\b', text)
            if uid_match:
                identifier = uid_match.group(0)
                id_type = 'uid'
    
    if not identifier:
        send_message('Gửi username Facebook (vd: zuck) hoặc URL hoặc UID')
        return {'statusCode': 200, 'body': 'OK'}
    
    send_message('⏳ Đang lấy thông tin...')
    
    try:
        if id_type == 'uid':
            fb_id = identifier
        else:
            url = f'https://graph.facebook.com/{identifier}?access_token={fb_token}&fields=id'
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200:
                send_message(f'❌ Không tìm thấy username: {identifier}')
                return {'statusCode': 200, 'body': 'OK'}
            fb_id = resp.json().get('id')
        
        fields = 'id,name,username,first_name,last_name,about,birthday,gender,location,hometown,email,website,relationship_status,political,religion,link,verified,created_time,followers_count'
        url = f'https://graph.facebook.com/{fb_id}?access_token={fb_token}&fields={fields}'
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            send_message(f'❌ Lỗi API: {resp.status_code}')
            return {'statusCode': 200, 'body': 'OK'}
        
        data = resp.json()
        
        # Lấy bài viết
        posts_url = f'https://graph.facebook.com/{fb_id}/posts?access_token={fb_token}&fields=id,message,created_time,likes.summary(true),comments.summary(true)&limit=3'
        posts_resp = requests.get(posts_url, timeout=10)
        posts = posts_resp.json().get('data', []) if posts_resp.status_code == 200 else []
        
        # Định dạng kết quả
        lines = []
        lines.append('📌 THÔNG TIN CÔNG KHAI')
        lines.append(f"ID: {data.get('id', 'N/A')}")
        lines.append(f"Tên: {data.get('name', 'N/A')}")
        lines.append(f"Username: {data.get('username', 'N/A')}")
        lines.append(f"Giới tính: {data.get('gender', 'N/A')}")
        lines.append(f"Ngày sinh: {data.get('birthday', 'N/A')}")
        loc = data.get('location', {})
        lines.append(f"Nơi sống: {loc.get('name', 'N/A') if isinstance(loc, dict) else loc}")
        lines.append(f"Xác thực: {'✅' if data.get('verified') else '❌'}")
        lines.append('')
        lines.append('📝 BÀI VIẾT GẦN ĐÂY:')
        
        if posts:
            for i, post in enumerate(posts[:3], 1):
                msg = post.get('message', '[Không có text]')[:100]
                time = post.get('created_time', 'N/A')[:16]
                likes = post.get('likes', {}).get('summary', {}).get('total_count', 0)
                comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                lines.append(f"{i}. {time}")
                lines.append(f"   {msg}")
                lines.append(f"   👍 {likes} 💬 {comments}")
        else:
            lines.append('Không có bài viết công khai')
        
        result = '\n'.join(lines)
        if len(result) > 4000:
            result = result[:3950] + '\n\n... (cắt)'
        
        send_message(result)
        
    except Exception as e:
        send_message(f'⚠️ Lỗi: {str(e)[:50]}')
    
    return {'statusCode': 200, 'body': 'OK'}
