# app.py — Clean UI: Upload -> Play -> A* (no deprecated params)
import streamlit as st
from PIL import Image
import io, hashlib
from typing import Tuple

from puzzle import (
    GOAL, is_solved, is_solvable, a_star,
    can_slide, slide_if_adjacent, scramble_via_random_walk
)
from image_utils import square_and_resize, slice_into_tiles, render_grid

State = Tuple[int, ...]

st.set_page_config(page_title="8-Puzzle — Upload • Play • A*", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1100px; padding-top: 0.5rem;}
.card {padding: 1rem; border-radius: 14px; background: rgba(200,200,200,0.06); border: 1px solid rgba(255,255,255,0.08);}
</style>
""", unsafe_allow_html=True)


def init_state():
    st.session_state.setdefault("tiles", None)
    st.session_state.setdefault("current", GOAL)
    st.session_state.setdefault("solution", [])
    st.session_state.setdefault("metrics", {})
    st.session_state.setdefault("step_idx", 0)
    st.session_state.setdefault("img_hash", None)
    st.session_state.setdefault("show_numbers", True)
    st.session_state.setdefault("orig_img", None)
    st.session_state.setdefault("show_guide_bg", True)
init_state()

st.title("8-Puzzle: Upload → Play → A* Solver")


with st.sidebar:
    st.header("1) Upload")
    up = st.file_uploader("PNG/JPG", type=["png","jpg","jpeg"], key="uploader")
    if up is not None:
        data = up.getvalue()
        h = hashlib.md5(data).hexdigest()
        if st.session_state.img_hash != h:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            img = square_and_resize(img, 540)
            st.session_state.orig_img = img
            st.session_state.tiles = slice_into_tiles(img)
            st.session_state.current = GOAL
            st.session_state.solution = []
            st.session_state.metrics = {}
            st.session_state.step_idx = 0
            st.session_state.img_hash = h
            st.success("Image sliced into 3×3 tiles.")

    st.divider()
    st.header("2) Shuffle")
    steps = st.slider("Difficulty (steps from goal)", 10, 120, 40, 10)
    if st.button("🔀 Shuffle (solvable)"):
        if st.session_state.tiles is None:
            st.warning("Upload an image first.")
        else:
            st.session_state.current = scramble_via_random_walk(steps=steps)
            st.session_state.solution = []
            st.session_state.metrics = {}
            st.session_state.step_idx = 0
            st.toast(f"Shuffled with {steps} steps", icon="🎲")

    st.divider()
    st.header("3) Solve")
    if st.button("🧠 Solve with A*"):
        if st.session_state.tiles is None:
            st.warning("Upload an image first.")
        else:
            start = st.session_state.current
            if not is_solvable(start):
                st.error("Not solvable (unexpected with Shuffle). Shuffle again.")
            else:
                with st.spinner("A* (Manhattan)…"):
                    path, metrics = a_star(start)
                if not path:
                    st.error("No solution found.")
                else:
                    st.session_state.solution = path
                    st.session_state.metrics = metrics
                    st.session_state.step_idx = 0
                    st.success(f"Solved in {metrics['length']} moves — expanded {metrics['expanded']} nodes.")

    st.divider()
    st.header("4) Options")
    st.session_state.show_numbers = st.checkbox("Show numbers on tiles", value=st.session_state.show_numbers)
    if st.button("↩ Reset to Goal"):
        st.session_state.current = GOAL
        st.session_state.solution = []
        st.session_state.metrics = {}
        st.session_state.step_idx = 0


col_left, col_right = st.columns([0.62, 0.38])

with col_left:
    st.subheader("Board")
    if st.session_state.tiles is None:
        st.info("Upload an image to begin.")
        st.caption("Or")
        st.info("Select default images")
        st.divider()
        st.subheader("Default images")

        
        def crop_and_resize(path, size=(1000, 1000)):
            img = Image.open(path).convert("RGB")
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            img = img.crop((left, top, right, bottom))
            return img.resize(size)

        default_paths = [
            "static/nature.jpeg",
            "static/boat.avif",
            "static/mountain.avif",
            "static/elephant.jpg"
        ]
        default_images = [(path, crop_and_resize(path)) for path in default_paths]
        cols = st.columns(4)

        for i, (path, img) in enumerate(default_images):
            with cols[i]:
                st.image(img, use_container_width=False)
                if st.button(f"{i+1}", key=f"default_{i}"):
                    img = square_and_resize(Image.open(path).convert("RGB"), 540)
                    st.session_state.orig_img = img
                    st.session_state.tiles = slice_into_tiles(img)
                    st.session_state.current = GOAL
                    st.session_state.solution = []
                    st.session_state.metrics = {}
                    st.session_state.step_idx = 0
                    st.session_state.img_hash = f"default_{i}"
                    st.success(f"Default image {i+1} sliced into 3×3 tiles.")
                    st.rerun()

    else:
        showing = st.session_state.solution[st.session_state.step_idx] if st.session_state.solution else st.session_state.current
        board_img = render_grid(
            showing,
            st.session_state.tiles,
            show_numbers=st.session_state.show_numbers,
            background=st.session_state.orig_img if st.session_state.show_guide_bg else None,
            blur_radius=8,
            tile_alpha=235 if st.session_state.show_guide_bg else 255
        )
        st.image(board_img, caption="3×3 tiles (bottom-right is the blank)", use_container_width=True)

with col_right:
    st.subheader("Play")
    if st.session_state.tiles is None:
        st.info("Upload an image to enable moves.")
    else:
        if st.session_state.solution:
            st.info("Viewing solution steps. Use the slider below or Reset to Goal to play.")
        else:
            cur = st.session_state.current
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write("Click a tile adjacent to the blank to slide it.")
            for r in range(3):
                cols = st.columns(3, gap="small")
                for c in range(3):
                    i = r*3 + c
                    val = cur[i]
                    label = "Blank" if val == 0 else f"Tile {val}"
                    with cols[c]:
                        if st.button(label, key=f"tile-{i}", use_container_width=True):
                            if can_slide(cur, i):
                                st.session_state.current = slide_if_adjacent(cur, i)
                                st.session_state.solution = []
                                st.session_state.metrics = {}
                                st.session_state.step_idx = 0
                                st.rerun()
                            else:
                                st.toast("Pick a tile next to the blank.", icon="⚠️")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.solution:
                st.subheader("Solution playback")
                n = len(st.session_state.solution)
                st.session_state.step_idx = st.slider("Step", 0, n - 1, st.session_state.step_idx, 1, key="playback")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("⏮ Prev"):
                        st.session_state.step_idx = max(0, st.session_state.step_idx - 1)
                with c2:
                    if st.button("⏭ Next"):
                        st.session_state.step_idx = min(n - 1, st.session_state.step_idx + 1)
                with c3:
                    if st.button("⏹ Reset to Start"):
                        st.session_state.step_idx = 0

                
            st.divider()
            show_original = st.toggle("Show original image")
            if show_original and st.session_state.orig_img is not None:
                st.image(st.session_state.orig_img, caption="Original image", use_container_width=True)


if st.session_state.solution:
    st.subheader("Solution playback")
    n = len(st.session_state.solution)
    st.session_state.step_idx = st.slider("Step", 0, n-1, st.session_state.step_idx, 1, key="playback")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⏮ Prev"):
            st.session_state.step_idx = max(0, st.session_state.step_idx - 1)
    with c2:
        if st.button("⏭ Next"):
            st.session_state.step_idx = min(n-1, st.session_state.step_idx + 1)
    with c3:
        if st.button("⏹ Reset to Start"):
            st.session_state.step_idx = 0
