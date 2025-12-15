import streamlit as st
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client
import json
from datetime import datetime
import uuid # <--- THÊM MỚI
import mimetypes # <--- THÊM MỚI
import time

BUCKET_NAME = "images" 

# Tạo User ID giả lập (Lưu trong Session State để không bị đổi mỗi khi reload)
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# ================= CẤU HÌNH =================
SUPABASE_URL = "https://aaezaowgeonxzpcafesa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhZXphb3dnZW9ueHpwY2FmZXNhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTA5MjU5OCwiZXhwIjoyMDgwNjY4NTk4fQ.pEFtqrjof9CwaHgKPNvhrfZvW1dE535bEme4BHZrV8c"

# Khởi tạo Supabase client
@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ================= CATEGORIES =================
CATEGORIES = {
    "Tất cả": None,
    "🏖️ Biển & Bãi Biển": "Biển & Bãi Biển",
    "⛰️ Núi & Thiên Nhiên": "Núi & Thiên Nhiên",
    "🛕 Chùa & Đền Thờ": "Chùa & Đền Thờ",
    "🏛️ Di Tích Lịch Sử": "Di Tích Lịch Sử",
    "🏛️ Bảo Tàng & Triển Lãm": "Bảo Tàng & Triển Lãm",
    "🌳 Công Viên & Vườn": "Công Viên & Vườn",
    "🍜 Nhà Hàng & Ẩm Thực": "Nhà Hàng & Ẩm Thực",
    "☕ Café & Bar": "Café & Bar",
    "🏨 Khách Sạn & Resort": "Khách Sạn & Resort",
    "🛍️ Trung Tâm Thương Mại": "Trung Tâm Thương Mại",
    "🎢 Giải Trí & Vui Chơi": "Giải Trí & Vui Chơi",
    "🎭 Trung Tâm Văn Hóa": "Trung Tâm Văn Hóa",
    "🦁 Sở Thú & Thủy Cung": "Sở Thú & Thủy Cung",
    "💧 Thác Nước & Hồ": "Thác Nước & Hồ",
    "🌅 Điểm Ngắm Cảnh": "Điểm Ngắm Cảnh",
}

SORT_OPTIONS = {
    "Đánh giá cao nhất": "rating",
    "Phổ biến nhất": "popularity",
    "Gần nhất": "distance",
}

# ================= API FUNCTIONS =================
def get_places(location=None, lat=None, lon=None, categories=None, 
               min_rating=0, max_distance=None, price_levels=None,
               amenities=None, sort_options=None, limit=20):
    """Gọi function get_places_advanced_v2 từ Supabase"""
    try:
        params = {
            "p_location": location if location else None,
            "p_lat": float(lat) if lat is not None else None,
            "p_lon": float(lon) if lon is not None else None,
            "p_categories": categories if categories else None,
            "p_min_rating": float(min_rating) if min_rating else None,
            "p_max_distance": int(max_distance * 1000) if max_distance else None,
            "p_price_levels": price_levels if price_levels else None,
            "p_amenities_jsonb": amenities if amenities else None,
            "p_sort_options": sort_options if sort_options else ["rating_desc"],
            "p_limit": int(limit)
        }
        
        # Gọi function RPC
        response = supabase.rpc("get_places_advanced_v2", params).execute()
        
        # Debug: kiểm tra dữ liệu trả về
        if hasattr(response, 'data'):
            return response.data
        elif hasattr(response, 'result'):
            return response.result()
        else:
            st.error(f"Không có dữ liệu trả về: {response}")
            return []
            
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {e}")
        return []

def get_comments(place_id, limit=10, offset=0, order_by="newest"):
    """Gọi function get_comments_by_place từ Supabase"""
    try:
        # Xử lý place_id có thể là uuid hoặc integer
        # Chuyển đổi order_by từ tiếng Việt sang tham số function
        order_map = {
            "Mới nhất": "recent",
            "Đánh giá cao nhất": "rating_desc", 
            "Đánh giá thấp nhất": "rating_asc"
        }
        
        params = {
            "p_place_id": place_id,  # Giữ nguyên, không convert
            "p_limit": int(limit),
            "p_offset": int(offset),
            "p_order_by": order_map.get(order_by, "recent")
        }
        
        # Debug
        st.write(f"Gọi get_comments_by_place với params: {params}")
        
        response = supabase.rpc("get_comments_by_place", params).execute()
        
        if hasattr(response, 'data'):
            return response.data
        else:
            st.error(f"Không có dữ liệu comments: {response}")
            return []
            
    except Exception as e:
        st.error(f"Lỗi khi lấy comments: {e}")
        return []

# ================= API FUNCTIONS =================
def get_places(location=None, lat=None, lon=None, categories=None, 
               min_rating=0, max_distance=None, price_levels=None,
               amenities=None, sort_options=None, limit=20):
    """Gọi function get_places_advanced_v2 từ Supabase"""
    try:
        params = {
            "p_location": location if location else None,
            "p_lat": float(lat) if lat is not None else None,
            "p_lon": float(lon) if lon is not None else None,
            "p_categories": categories if categories else None,
            "p_min_rating": float(min_rating) if min_rating else None,
            "p_max_distance": int(max_distance * 1000) if max_distance else None,
            "p_price_levels": price_levels if price_levels else None,
            "p_amenities_jsonb": amenities if amenities else None,
            "p_sort_options": [sort_options] if sort_options else ["rating"],
            "p_limit": int(limit)
        }
        
        # Gọi function RPC
        response = supabase.rpc("get_places_advanced_v2", params).execute()
        
        # Debug
        if hasattr(response, 'data'):
            data = response.data
            return data
        else:
            st.error(f"Không có dữ liệu trả về: {response}")
            return []
            
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {e}")
        return []

def get_comments(place_id, limit=10, offset=0, order_by="newest"):
    """Gọi function get_comments_by_place từ Supabase"""
    try:
        # Xử lý order_by từ tiếng Việt sang tham số function
        order_map = {
            "Mới nhất": "recent",
            "Đánh giá cao nhất": "rating_desc", 
            "Đánh giá thấp nhất": "rating_asc"
        }
        
        # Query trực tiếp comments table
        query = supabase.table('comments').select('*').eq('place_id', place_id)
        
        # --- SỬA LỖI TẠI ĐÂY ---
        if order_by == "recent":
            query = query.order('date', desc=True)
        elif order_by == "rating_desc":
            query = query.order('rating', desc=True)
        elif order_by == "rating_asc":
            # SAI: query = query.order('rating', asc=True)
            # ĐÚNG: dùng desc=False
            query = query.order('rating', desc=False) 
        # -----------------------

        # Áp dụng limit và offset
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        if hasattr(response, 'data'):
            comments = response.data
            
            # Lấy ảnh cho từng comment
            for comment in comments:
                comment_id = comment.get('id')
                img_response = supabase.table('images').select('*').eq('comment_id', comment_id).execute()
                if hasattr(img_response, 'data') and img_response.data:
                    comment['images'] = img_response.data
                else:
                    comment['images'] = []
            
            return comments
        else:
            return []
            
    except Exception as e:
        st.error(f"Lỗi khi lấy comments: {e}")
        return []

# ================= UI COMPONENTS =================
def render_image_carousel(images, key_prefix=""):
    """Render ảnh carousel với tất cả hình ảnh"""
    if not images or len(images) == 0:
        st.image("https://via.placeholder.com/400x300?text=No+Image", use_container_width=True)
        return
    
    # Debug: hiển thị số lượng ảnh
    st.write(f"🎞️ Carousel có {len(images)} ảnh")
    
    # Nếu chỉ có 1 ảnh
    if len(images) == 1:
        img_url = images[0].get('url', '')
        if img_url:
            try:
                st.image(img_url, use_container_width=True)
            except Exception as e:
                st.warning(f"Không thể tải ảnh: {e}")
                st.image("https://via.placeholder.com/400x300?text=Image+Error", use_container_width=True)
        else:
            st.image("https://via.placeholder.com/400x300?text=No+Image", use_container_width=True)
        return
    
    # Carousel với session state - sử dụng key duy nhất
    carousel_key = f"carousel_index_{key_prefix}"
    
    # Khởi tạo hoặc reset index
    if carousel_key not in st.session_state:
        st.session_state[carousel_key] = 0
    
    current_idx = st.session_state[carousel_key]
    
    # Tạo layout cho carousel
    col1, col2, col3 = st.columns([1, 8, 1])
    
    # Nút Previous (Trái)
    with col1:
        if st.button("◀", key=f"prev_{key_prefix}", help="Ảnh trước"):
            if current_idx > 0:
                st.session_state[carousel_key] = current_idx - 1
            else:
                st.session_state[carousel_key] = len(images) - 1  # Quay lại ảnh cuối
            st.rerun()
    
    # Hiển thị ảnh hiện tại
    with col2:
        img_url = images[current_idx].get('url', '')
        st.write(f"**Ảnh {current_idx + 1}/{len(images)}**")
        
        if img_url:
            try:
                st.image(img_url, use_container_width=True, caption=f"Ảnh {current_idx + 1}/{len(images)}")
            except Exception as e:
                st.error(f"Không thể tải ảnh {current_idx + 1}: {img_url}")
                st.image("https://via.placeholder.com/400x300?text=Image+Error", 
                         use_container_width=True, 
                         caption=f"Lỗi tải ảnh {current_idx + 1}")
        else:
            st.image("https://via.placeholder.com/400x300?text=No+Image", 
                     use_container_width=True, 
                     caption=f"Không có URL ảnh {current_idx + 1}")
    
    # Nút Next (Phải)
    with col3:
        if st.button("▶", key=f"next_{key_prefix}", help="Ảnh tiếp theo"):
            if current_idx < len(images) - 1:
                st.session_state[carousel_key] = current_idx + 1
            else:
                st.session_state[carousel_key] = 0  # Quay lại ảnh đầu
            st.rerun()
    
    # Thêm nút chuyển nhanh cho carousel (nếu có nhiều ảnh)
    if len(images) > 5:
        st.markdown("### 🔍 Chuyển nhanh đến ảnh:")
        
        # Chia thành các hàng, mỗi hàng 5 nút
        cols_per_row = 5
        rows = (len(images) + cols_per_row - 1) // cols_per_row
        
        for row in range(rows):
            cols = st.columns(cols_per_row)
            start_idx = row * cols_per_row
            
            for i in range(cols_per_row):
                img_idx = start_idx + i
                if img_idx < len(images):
                    with cols[i]:
                        if st.button(f"{img_idx + 1}", key=f"jump_{key_prefix}_{img_idx}"):
                            st.session_state[carousel_key] = img_idx
                            st.rerun()

def render_star_rating(rating):
    """Render rating dạng sao"""
    if rating is None:
        return "Chưa có đánh giá"
    
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    return "⭐" * full_stars + "✨" * half_star + "☆" * empty_stars + f" ({rating:.1f})"

def render_place_card(place, index):
    """Render card cho mỗi địa điểm"""
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            images = place.get('images', [])
            if images and len(images) > 0:
                # Hiển thị ảnh đầu tiên
                st.image(images[0].get('url', 'https://via.placeholder.com/300x200'), 
                        use_container_width=True)
                if len(images) > 1:
                    st.caption(f"📷 +{len(images) - 1} ảnh khác")
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image", 
                        use_container_width=True)
        
        with col2:
            st.subheader(place.get('name', 'N/A'))
            
            # Category badge
            category = place.get('category', 'N/A')
            st.markdown(f"🏷️ **{category}**")
            
            # Rating
            rating = place.get('rating')
            rating_count = place.get('rating_count', 0)
            st.markdown(f"{render_star_rating(rating)} - {rating_count} đánh giá")
            
            # Address
            address = place.get('address', 'N/A')
            st.markdown(f"📍 {address[:80]}..." if len(address) > 80 else f"📍 {address}")
            
            # Distance (nếu có)
            distance = place.get('distance_km')
            if distance:
                st.markdown(f"📏 Cách bạn **{distance} km**")
            
            # Button xem chi tiết
            if st.button(f"👁️ Xem chi tiết", key=f"view_{index}"):
                st.session_state.selected_place = place
                st.session_state.show_detail = True
                st.rerun()
        
        st.divider()

def render_place_detail(place):
    """Render trang chi tiết địa điểm (Giữ nguyên layout cũ, thêm Form upload)"""
    
    # --- PHẦN 1: LOGIC CŨ (GIỮ NGUYÊN) ---
    # Back button
    if st.button("← Quay lại"):
        st.session_state.show_detail = False
        st.session_state.selected_place = None
        st.rerun()
    
    st.title(place.get('name', 'N/A'))
    
    # Image carousel
    images = place.get('images', [])
    render_image_carousel(images, key_prefix=str(place.get('id', 'detail')))
    
    # Info columns (Logic cũ của bạn)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Thông tin")
        st.markdown(f"**Danh mục:** {place.get('category', 'N/A')}")
        st.markdown(f"**Đánh giá:** {render_star_rating(place.get('rating'))}")
        st.markdown(f"**Số lượt đánh giá:** {place.get('rating_count', 0)}")
        
        if place.get('phone'):
            st.markdown(f"**📞 Điện thoại:** {place.get('phone')}")
        if place.get('website'):
            st.markdown(f"**🌐 Website:** [{place.get('website')}]({place.get('website')})")
    
    with col2:
        st.markdown("### 📍 Địa chỉ")
        st.markdown(place.get('address', 'N/A'))
        
        # Opening hours
        opening_hours = place.get('opening_hours')
        if opening_hours:
            st.markdown("### 🕐 Giờ mở cửa")
            if isinstance(opening_hours, dict):
                for day, hours in opening_hours.items():
                    st.markdown(f"- **{day}:** {hours}")
            else:
                st.markdown(str(opening_hours))
    
    # About section (Logic cũ của bạn)
    about = place.get('about')
    if about:
        st.markdown("### ℹ️ Giới thiệu")
        if isinstance(about, dict):
            st.json(about)
        else:
            st.markdown(str(about))
    
    # Mini map (Logic cũ của bạn)
    coordinates = place.get('coordinates')
    if coordinates:
        st.markdown("### 🗺️ Vị trí trên bản đồ")
        lat = coordinates.get('lat')
        lon = coordinates.get('lon')
        if lat and lon:
            mini_map = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker(
                [lat, lon],
                popup=place.get('name'),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(mini_map)
            st_folium(mini_map, width=700, height=300)
    
    st.markdown("---")

    # --- PHẦN 2: FORM ĐÁNH GIÁ (MỚI THÊM VÀO) ---
    st.subheader("✍️ Viết đánh giá & Check-in")
    
    with st.container(border=True): # Đóng khung cho đẹp
        with st.form(key="review_form"):
            f_col1, f_col2 = st.columns([1, 1])
            
            with f_col1:
                input_name = st.text_input("Tên hiển thị", value="Khách tham quan")
                input_rating = st.slider("Chấm điểm", 0, 5, 5)
            
            with f_col2:
                # Input upload ảnh
                input_files = st.file_uploader("Chia sẻ hình ảnh (tối đa 5 ảnh)", 
                                             type=['png', 'jpg', 'jpeg'], 
                                             accept_multiple_files=True)
            
            input_text = st.text_area("Nội dung đánh giá", placeholder="Chia sẻ trải nghiệm của bạn...")
            
            submit_btn = st.form_submit_button("Gửi đánh giá", type="primary", use_container_width=True)
            
            if submit_btn:
                # Xử lý sự kiện gửi
                if 'user_id' not in st.session_state:
                    import uuid
                    st.session_state.user_id = str(uuid.uuid4())

                # Validate
                if not input_text and not input_files:
                    st.warning("Vui lòng nhập nội dung hoặc tải ảnh lên!")
                else:
                    # Gọi hàm xử lý (đã viết ở bước trước)
                    success, msg = submit_review(
                        place_id=place.get('id'),
                        user_id=st.session_state.user_id,
                        author_name=input_name,
                        rating=input_rating,
                        text=input_text,
                        files=input_files
                    )
                    
                    if success:
                        st.success(f"🎉 {msg}")
                        time.sleep(1) 
                        st.rerun() # Reload để hiện comment mới
                    else:
                        st.error(f"⚠️ {msg}")

    # --- PHẦN 3: DANH SÁCH COMMENT (GIỮ LOGIC CŨ + FIX HTTPS) ---
    st.markdown("### 💬 Đánh giá & Bình luận")
    
    # Sort comments
    comment_sort = st.selectbox(
        "Sắp xếp theo:",
        ["Mới nhất", "Đánh giá cao nhất", "Đánh giá thấp nhất"],
        key="comment_sort"
    )
    
    sort_map = {
        "Mới nhất": "recent",
        "Đánh giá cao nhất": "rating_desc",
        "Đánh giá thấp nhất": "rating_asc"
    }
    
    comments = get_comments(place.get('id'), limit=20, order_by=sort_map[comment_sort])
    
    if not comments:
        st.info("Chưa có đánh giá nào cho địa điểm này.")
    else:
        for comment in comments:
            with st.container():
                # Comment header
                col1, col2 = st.columns([3, 1])
                with col1:
                    author = comment.get('author', 'Ẩn danh')
                    st.markdown(f"**👤 {author}**")
                with col2:
                    comment_rating = comment.get('rating')
                    if comment_rating:
                        st.markdown(f"⭐ {comment_rating:.1f}")
                
                # Comment date
                date = comment.get('date')
                if date:
                    st.caption(f"📅 {date}")
                
                # Comment text
                text = comment.get('text')
                if text:
                    st.markdown(text)
                
                # Comment images (CÓ FIX LỖI HTTP)
                comment_images = comment.get('images', [])
                if comment_images and len(comment_images) > 0:
                    st.markdown("**📸 Ảnh đính kèm:**")
                    img_cols = st.columns(min(len(comment_images), 4))
                    for idx, img in enumerate(comment_images[:4]):
                        with img_cols[idx]:
                            img_url = img.get('url', '')
                            
                            # --- ĐOẠN NÀY QUAN TRỌNG: FIX HTTPS ---
                            if img_url and img_url.startswith("http://"):
                                img_url = img_url.replace("http://", "https://")
                            # --------------------------------------
                            
                            if img_url:
                                st.image(img_url, use_container_width=True)
                
                st.divider()

def render_map(places, user_lat=None, user_lon=None):
    """Render bản đồ với markers"""
    # Tâm bản đồ
    if user_lat and user_lon:
        center = [user_lat, user_lon]
        zoom = 13
    elif places and len(places) > 0:
        # Lấy tâm từ place đầu tiên
        first_place = places[0]
        coords = first_place.get('coordinates', {})
        center = [coords.get('lat', 16.0), coords.get('lon', 108.0)]
        zoom = 12
    else:
        center = [16.0544, 108.2022]  # Đà Nẵng
        zoom = 12
    
    # Tạo map
    m = folium.Map(location=center, zoom_start=zoom)
    
    # User marker
    if user_lat and user_lon:
        folium.Marker(
            [user_lat, user_lon],
            popup="📍 Vị trí của bạn",
            icon=folium.Icon(color='blue', icon='user')
        ).add_to(m)
    
    # Place markers
    for place in places:
        coords = place.get('coordinates', {})
        lat = coords.get('lat')
        lon = coords.get('lon')
        
        if lat and lon:
            # Popup content
            popup_html = f"""
            <div style="width:200px">
                <b>{place.get('name', 'N/A')}</b><br>
                <small>{place.get('category', '')}</small><br>
                ⭐ {place.get('rating', 'N/A')} ({place.get('rating_count', 0)} đánh giá)<br>
                📍 {place.get('address', '')[:50]}...
            </div>
            """
            
            # Icon color theo category
            color = 'red'
            if 'Biển' in str(place.get('category', '')):
                color = 'blue'
            elif 'Núi' in str(place.get('category', '')):
                color = 'green'
            elif 'Chùa' in str(place.get('category', '')) or 'Đền' in str(place.get('category', '')):
                color = 'orange'
            elif 'Nhà Hàng' in str(place.get('category', '')) or 'Café' in str(place.get('category', '')):
                color = 'purple'
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)
    
    return m

# ================= NEW FUNCTIONS: UPLOAD & SUBMIT =================

def upload_images_to_storage(files):
    """Upload list file lên Supabase Storage và trả về list URL"""
    image_urls = []
    
    if not files:
        return []

    for file in files:
        try:
            # Tạo tên file unique để không bị trùng
            file_ext = mimetypes.guess_extension(file.type) or ".jpg"
            file_name = f"reviews/{int(time.time())}_{uuid.uuid4()}{file_ext}"
            
            # Upload file
            # Lưu ý: file.getvalue() để lấy data binary từ Streamlit uploader
            res = supabase.storage.from_(BUCKET_NAME).upload(
                path=file_name,
                file=file.getvalue(),
                file_options={"content-type": file.type}
            )
            
            # Lấy Public URL
            public_url_data = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
            
            # Supabase-py v2 trả về string URL trực tiếp hoặc object tùy phiên bản
            # Code này xử lý cả 2 trường hợp
            if isinstance(public_url_data, str):
                image_urls.append(public_url_data)
            elif hasattr(public_url_data, 'public_url'): # Phiên bản cũ hơn
                 image_urls.append(public_url_data.public_url)
            else:
                 # Trường hợp data trả về là public_url string nằm trong biến data (bản mới nhất)
                 image_urls.append(public_url_data)

        except Exception as e:
            st.error(f"Lỗi upload ảnh {file.name}: {e}")
            return None # Trả về None để báo lỗi
            
    return image_urls

def submit_review(place_id, user_id, author_name, rating, text, files):
    """Xử lý toàn bộ quy trình: Upload ảnh -> Gọi RPC lưu DB"""
    
    # 1. Upload ảnh (nếu có)
    image_urls = []
    if files:
        with st.spinner("Đang tải ảnh lên..."):
            image_urls = upload_images_to_storage(files)
            if image_urls is None: # Có lỗi upload
                return False, "Lỗi khi tải ảnh lên server."
    
    # 2. Gọi RPC create_user_content
    try:
        params = {
            "p_place_id": place_id,
            "p_user_id": user_id,
            "p_author_name": author_name,
            "p_rating": rating,
            "p_text": text,
            "p_image_urls": image_urls
        }
        
        # Gọi RPC
        response = supabase.rpc("create_user_content", params).execute()
        
        # Kiểm tra kết quả
        if hasattr(response, 'data') and response.data:
            # Function trả về row dạng (success, comment_id, ...)
            # Supabase-py thường trả về list các row
            result = response.data # Có thể là dict hoặc list
            
            # Xử lý trường hợp trả về list hoặc dict
            if isinstance(result, list) and len(result) > 0:
                 res_data = result[0]
            else:
                 res_data = result

            if res_data.get('success'):
                return True, res_data.get('message')
            else:
                return False, res_data.get('message')
        else:
            return False, "Không nhận được phản hồi từ server."
            
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"
    
    
# ================= MAIN APP =================
def main():
    st.set_page_config(
        page_title="🗺️ TrackAsia - Khám phá Việt Nam",
        page_icon="🗺️",
        layout="wide"
    )
    
    # Initialize session state
    if 'show_detail' not in st.session_state:
        st.session_state.show_detail = False
    if 'selected_place' not in st.session_state:
        st.session_state.selected_place = None
    
    # Show detail page if selected
    if st.session_state.show_detail and st.session_state.selected_place:
        render_place_detail(st.session_state.selected_place)
        return
    
    # Header
    st.title("🗺️ TrackAsia - Khám phá Việt Nam")
    st.markdown("Tìm kiếm và khám phá các địa điểm du lịch tuyệt vời trên khắp Việt Nam")
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Bộ lọc tìm kiếm")
        
        # Location search
        location = st.text_input("📍 Tìm theo địa điểm", placeholder="Ví dụ: Đà Nẵng, Hội An...")
        
        # Category filter
        selected_categories = st.multiselect(
            "🏷️ Danh mục",
            options=list(CATEGORIES.keys())[1:],  # Bỏ "Tất cả"
            default=[]
        )
        
        # Convert to category values
        category_values = [CATEGORIES[cat] for cat in selected_categories if CATEGORIES.get(cat)]
        
        # Rating filter
        min_rating = st.slider("⭐ Đánh giá tối thiểu", 0.0, 5.0, 0.0, 0.5)
        
        # Distance filter
        st.markdown("📏 **Khoảng cách**")
        use_location = st.checkbox("Sử dụng vị trí của tôi")
        
        user_lat = None
        user_lon = None
        max_distance = None
        
        if use_location:
            col1, col2 = st.columns(2)
            with col1:
                user_lat = st.number_input("Latitude", value=16.0544, format="%.4f")
            with col2:
                user_lon = st.number_input("Longitude", value=108.2022, format="%.4f")
            
            max_distance = st.slider("Trong bán kính (km)", 1, 100, 10)
        
        # Sort options
        st.markdown("📊 **Sắp xếp**")
        sort_option = st.selectbox(
            "Sắp xếp theo",
            options=list(SORT_OPTIONS.keys())
        )
        sort_value = SORT_OPTIONS[sort_option]
        
        # Limit
        limit = st.slider("Số kết quả", 10, 100, 20)
        
        # Search button
        search_clicked = st.button("🔍 Tìm kiếm", type="primary", use_container_width=True)
    
    # Main content
    col_list, col_map = st.columns([1, 1])
    
    # Fetch data
    places = get_places(
        location=location if location else None,
        lat=user_lat,
        lon=user_lon,
        categories=category_values if category_values else None,
        min_rating=min_rating,
        max_distance=max_distance,
        sort_options=[sort_value],
        limit=limit
    )
    
    with col_list:
        st.subheader(f"📋 Danh sách địa điểm ({len(places)} kết quả)")
        
        if not places:
            st.info("Không tìm thấy địa điểm nào. Hãy thử thay đổi bộ lọc!")
        else:
            # Scrollable list
            for idx, place in enumerate(places):
                render_place_card(place, idx)
    
    with col_map:
        st.subheader("🗺️ Bản đồ")
        
        # Render map
        map_obj = render_map(places, user_lat, user_lon)
        st_folium(map_obj, width=None, height=600)

if __name__ == "__main__":
    main()
