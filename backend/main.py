import json
import os
from typing import Any, List, Optional

from apify_client import ApifyClient
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Lodgic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

apify_client = ApifyClient(APIFY_TOKEN) if APIFY_TOKEN else None
ai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL) if OPENAI_API_KEY else None


class SearchRequest(BaseModel):
    location: str = Field(..., min_length=2)
    vibe: str = Field(..., min_length=8)
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    guests: int = Field(default=2, ge=1, le=16)
    max_price: Optional[int] = Field(default=None, ge=1)
    limit: int = Field(default=8, ge=1, le=30)


class MatchAnalysis(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    verdict: str
    matched: List[str] = []
    missing: List[str] = []
    cautions: List[str] = []


class Listing(BaseModel):
    id: str
    name: str
    url: str
    description: Optional[str] = None
    price: Optional[str] = None
    image: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    room_type: Optional[str] = None
    analysis: MatchAnalysis
    is_match: bool = False


def _dig(data: dict, *path: str, default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def _listing_id(item: dict) -> str:
    return str(item.get("id") or item.get("pdp_listing_id") or item.get("room_id") or "")


def _listing_url(item: dict) -> str:
    if item.get("url"):
        return item["url"]
    listing_id = _listing_id(item)
    return f"https://www.airbnb.com/rooms/{listing_id}" if listing_id else "https://www.airbnb.com"


def _listing_price(item: dict) -> str:
    price = item.get("price")
    if isinstance(price, str):
        return price
    formatted = _dig(item, "price", "rate", "amount_formatted")
    if formatted:
        return formatted
    amount = _dig(item, "price", "rate", "amount")
    currency = _dig(item, "price", "rate", "currency", default="$")
    return f"{currency}{amount}" if amount else "Price unavailable"


def _listing_text(item: dict) -> str:
    fields = [
        item.get("name"),
        item.get("title"),
        item.get("description"),
        item.get("roomType"),
        item.get("propertyType"),
        " ".join(item.get("amenities", [])[:20]) if isinstance(item.get("amenities"), list) else None,
        " ".join(review.get("comments", "") for review in item.get("reviews", [])[:5])
        if isinstance(item.get("reviews"), list)
        else None,
    ]
    return "\n".join(str(field) for field in fields if field)


def get_raw_listings(request: SearchRequest):
    if not apify_client:
        return [
            {
                "id": "farm-1",
                "name": "Quiet Farm Cottage with Sheep Paddock",
                "description": "A small cottage on a working family farm outside Leatherhead. Guests mention sheep in the field, dark skies, birdsong, fast Wi-Fi, and a desk by the window. No parties.",
                "url": "https://airbnb.com/rooms/farm-1",
                "thumbnail": "https://images.unsplash.com/photo-1500382017468-9049fed747ef",
                "price": {"rate": {"amount_formatted": "£128 night"}},
                "rating": 4.93,
                "reviewsCount": 87,
                "roomType": "Entire guesthouse",
                "amenities": ["Wi-Fi", "Kitchen", "Dedicated workspace", "Free parking", "Garden"],
            },
            {
                "id": "flat-2",
                "name": "Modern Central Flat near Station",
                "description": "Bright apartment close to shops, nightlife, and the train station. Convenient, stylish, and compact.",
                "url": "https://airbnb.com/rooms/flat-2",
                "thumbnail": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
                "price": {"rate": {"amount_formatted": "£95 night"}},
                "rating": 4.72,
                "reviewsCount": 112,
                "roomType": "Entire rental unit",
                "amenities": ["Wi-Fi", "Kitchen", "Washer"],
            },
            {
                "id": "barn-3",
                "name": "Converted Barn on Country Lane",
                "description": "Peaceful barn conversion with a fireplace and field views. Reviews praise the silence but note the road is narrow and there are no animals on site.",
                "url": "https://airbnb.com/rooms/barn-3",
                "thumbnail": "https://images.unsplash.com/photo-1518780664697-55e3ad937233",
                "price": {"rate": {"amount_formatted": "£154 night"}},
                "rating": 4.88,
                "reviewsCount": 43,
                "roomType": "Entire cottage",
                "amenities": ["Indoor fireplace", "Wi-Fi", "Dedicated workspace", "Free parking"],
            },
        ][: request.limit]

    run_input = {
        "location": request.location,
        "maxItems": request.limit,
        "adults": request.guests,
    }
    if request.check_in:
        run_input["checkIn"] = request.check_in
    if request.check_out:
        run_input["checkOut"] = request.check_out

    try:
        run = apify_client.actor("crawlerbros/airbnb-scraper").call(run_input=run_input)
        return list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception as exc:
        print(f"Apify error: {exc}")
        return []


def local_match_analysis(listing: dict, request: SearchRequest) -> MatchAnalysis:
    text = _listing_text(listing).lower()
    criteria = request.vibe.lower()
    score = 45
    matched = []
    missing = []
    cautions = []

    signals = {
        "quiet": ["quiet", "peaceful", "silence", "birdsong", "rural"],
        "farm or animals": ["farm", "sheep", "horse", "animals", "paddock"],
        "work friendly": ["wifi", "wi-fi", "desk", "workspace"],
        "nature": ["field", "garden", "country", "countryside"],
        "fireplace": ["fireplace", "wood burner", "stove"],
    }
    for label, words in signals.items():
        if any(word in criteria for word in words) and any(word in text for word in words):
            score += 12
            matched.append(label)
        elif any(word in criteria for word in words):
            score -= 8
            missing.append(label)

    if "station" in text or "nightlife" in text or "central" in text:
        score -= 15
        cautions.append("Urban convenience signals may conflict with a secluded stay.")
    if "no animals" in text:
        score -= 18
        cautions.append("Description says there are no animals on site.")

    score = max(0, min(100, score))
    verdict = "Strong fit" if score >= 75 else "Possible fit" if score >= 55 else "Weak fit"
    return MatchAnalysis(
        score=score,
        verdict=f"{verdict}: based on listing text and available amenities.",
        matched=matched[:4],
        missing=missing[:4],
        cautions=cautions[:3],
    )


def ai_match_analysis(listing: dict, request: SearchRequest) -> MatchAnalysis:
    if not ai_client:
        return local_match_analysis(listing, request)

    prompt = {
        "role": "user",
        "content": (
            "You are Lodgic, an Airbnb decision assistant. Score how well this listing matches the user's trip intent. "
            "Use only evidence present in the listing. Return strict JSON with keys: score integer 0-100, verdict string under 22 words, "
            "matched array of short evidence phrases, missing array of unmet needs, cautions array of risks or uncertainty.\n\n"
            f"User intent: {request.vibe}\n"
            f"Location: {request.location}\n"
            f"Guests: {request.guests}\n"
            f"Max nightly price: {request.max_price or 'not provided'}\n"
            f"Listing:\n{_listing_text(listing)[:5000]}"
        ),
    }

    try:
        response = ai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[prompt],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return MatchAnalysis(
            score=int(data.get("score", 0)),
            verdict=str(data.get("verdict", "No verdict returned.")),
            matched=list(data.get("matched", []))[:5],
            missing=list(data.get("missing", []))[:5],
            cautions=list(data.get("cautions", []))[:4],
        )
    except Exception as exc:
        print(f"AI error: {exc}")
        fallback = local_match_analysis(listing, request)
        fallback.cautions.append("AI analysis failed; using local keyword fallback.")
        return fallback


@app.get("/")
async def root():
    return {"message": "Lodgic API is running", "model": OPENAI_MODEL}


@app.post("/search", response_model=List[Listing])
async def search(request: SearchRequest):
    raw_results = get_raw_listings(request)
    processed_results = []

    for item in raw_results:
        analysis = ai_match_analysis(item, request)
        listing = Listing(
            id=_listing_id(item),
            name=item.get("name") or item.get("title") or "Unknown Listing",
            url=_listing_url(item),
            description=item.get("description", ""),
            price=_listing_price(item),
            image=item.get("thumbnail") or item.get("picture_url") or item.get("image"),
            rating=item.get("rating") or item.get("avgRating"),
            review_count=item.get("reviewsCount") or item.get("reviews_count"),
            room_type=item.get("roomType") or item.get("propertyType"),
            analysis=analysis,
            is_match=analysis.score >= 70,
        )
        processed_results.append(listing)

    return sorted(processed_results, key=lambda result: result.analysis.score, reverse=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
