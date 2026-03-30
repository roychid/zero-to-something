from flask import Flask, jsonify
from flask_cors import CORS
import requests
import traceback
import os

app = Flask(__name__)
CORS(app)

# Get API key from environment variable (set in Vercel dashboard)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "b1d4f776c5msh0a5a6ce81cd9670p1e5ae8jsn169c02186937")
USERNAME = "neogreats"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "instagram120.p.rapidapi.com",
    "Content-Type": "application/json"
}

def safe_get(obj, *keys, default=None):
    """Safely traverse nested dict/list."""
    for key in keys:
        try:
            obj = obj[key]
        except (KeyError, IndexError, TypeError):
            return default
    return obj if obj is not None else default

@app.route('/api/instagram/all', methods=['GET'])
def get_all():
    try:
        # ── 1. USER INFO ──────────────────────────────────────────
        user_res = requests.post(
            "https://instagram120.p.rapidapi.com/api/instagram/userInfo",
            json={"username": USERNAME},
            headers=HEADERS,
            timeout=15
        )
        user_res.raise_for_status()
        user_raw = user_res.json()

        raw_result = user_raw.get("result", [])
        if isinstance(raw_result, list) and len(raw_result) > 0:
            user_result = raw_result[0].get("user", raw_result[0])
        elif isinstance(raw_result, dict):
            user_result = raw_result.get("user", raw_result)
        else:
            user_result = {}

        user = {
            "username":    user_result.get("username", USERNAME),
            "full_name":   user_result.get("full_name", "NEOGREATS"),
            "bio":         user_result.get("biography", "Zero to Something — documenting the journey"),
            "followers":   user_result.get("follower_count", 0),
            "following":   user_result.get("following_count", 0),
            "posts":       user_result.get("media_count", 0),
            "profile_pic": user_result.get("profile_pic_url", ""),
            "external_url": user_result.get("external_url", ""),
            "is_verified": user_result.get("is_verified", False),
            "category":    user_result.get("category", ""),
        }

        # ── 2. REELS ──────────────────────────────────────────────
        reels_res = requests.post(
            "https://instagram120.p.rapidapi.com/api/instagram/reels",
            json={"username": USERNAME, "maxId": ""},
            headers=HEADERS,
            timeout=15
        )
        reels_res.raise_for_status()
        reels_raw = reels_res.json()

        edges = (
            safe_get(reels_raw, "result", "edges", default=[]) or
            safe_get(reels_raw, "data", "edges", default=[]) or
            safe_get(reels_raw, "edges", default=[]) or
            safe_get(reels_raw, "reels", default=[]) or
            []
        )

        reels = []
        for edge in edges[:6]:
            node = edge.get("node", edge)
            media = node.get("media", node)

            video_url = None
            vid_versions = media.get("video_versions", [])
            if vid_versions:
                video_url = vid_versions[0].get("url")

            thumb = None
            img_candidates = safe_get(media, "image_versions2", "candidates", default=[])
            if img_candidates:
                thumb = img_candidates[0].get("url")

            caption_obj = media.get("caption") or {}
            caption = (
                caption_obj.get("text", "") if isinstance(caption_obj, dict)
                else str(caption_obj)
            )

            reels.append({
                "id":        media.get("id", ""),
                "code":      media.get("code", ""),
                "video_url": video_url,
                "thumbnail": thumb,
                "caption":   caption,
                "likes":     media.get("like_count", 0),
                "comments":  media.get("comment_count", 0),
                "plays":     media.get("play_count") or media.get("view_count", 0),
                "timestamp": media.get("taken_at", 0),
                "media_type": media.get("media_type", 0),
                "ig_link": f"https://www.instagram.com/reel/{media.get('code', '')}/" if media.get("code") else f"https://www.instagram.com/{USERNAME}/"
            })

        # ── 3. POSTS ──────────────────────────────────────────────
        posts_res = requests.post(
            "https://instagram120.p.rapidapi.com/api/instagram/posts",
            json={"username": USERNAME, "maxId": ""},
            headers=HEADERS,
            timeout=15
        )
        posts_raw = posts_res.json() if posts_res.ok else {}

        post_edges = (
            safe_get(posts_raw, "result", "edges", default=[]) or
            safe_get(posts_raw, "data", "edges", default=[]) or
            []
        )

        posts = []
        for edge in post_edges[:6]:
            node = edge.get("node", edge)
            media = node.get("media", node)

            img_candidates = safe_get(media, "image_versions2", "candidates", default=[])
            thumb = img_candidates[0].get("url") if img_candidates else None

            caption_obj = media.get("caption") or {}
            caption = (
                caption_obj.get("text", "") if isinstance(caption_obj, dict)
                else str(caption_obj)
            )

            posts.append({
                "id":        media.get("id", ""),
                "code":      media.get("code", ""),
                "thumbnail": thumb,
                "caption":   caption,
                "likes":     media.get("like_count", 0),
                "comments":  media.get("comment_count", 0),
                "timestamp": media.get("taken_at", 0),
                "ig_link": f"https://www.instagram.com/p/{media.get('code', '')}/" if media.get("code") else ""
            })

        followers = user.get("followers", 0)

        return jsonify({
            "success": True,
            "user": user,
            "reels": reels,
            "posts": posts,
            "stats": {
                "weeks":     142,
                "followers": followers,
                "community": followers,
                "courses":   4,
                "mentored":  200,
                "posts":     user.get("posts", 0),
            }
        })

    except requests.exceptions.RequestException as e:
        print("REQUEST ERROR:", traceback.format_exc())
        return jsonify({"success": False, "error": f"API request failed: {str(e)}"}), 500
    except Exception as e:
        print("ERROR:", traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/debug', methods=['GET'])
def debug():
    try:
        user_res = requests.post(
            "https://instagram120.p.rapidapi.com/api/instagram/userInfo",
            json={"username": USERNAME}, headers=HEADERS, timeout=15
        )
        reels_res = requests.post(
            "https://instagram120.p.rapidapi.com/api/instagram/reels",
            json={"username": USERNAME, "maxId": ""}, headers=HEADERS, timeout=15
        )
        return jsonify({
            "user_status": user_res.status_code,
            "user_raw": user_res.json(),
            "reels_status": reels_res.status_code,
            "reels_raw": reels_res.json()
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# Required for Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
