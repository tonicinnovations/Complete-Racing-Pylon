// tile90ccw.cc — rotate EACH 64x32 tile 90° CCW (per-panel), then stack with V-mapper.
#include "pixel-mapper.h"
using namespace rgb_matrix;

class Tile90CCW : public PixelMapper {
 public:
  Tile90CCW() : chain_(1), parallel_(1) {}

  const char *GetName() const override { return "Tile90CCW"; }

  // chain,parallel come from hardware config; we assume parallel==1
  bool SetParameters(int chain, int parallel, const char * /*param*/) override {
    chain_    = (chain    > 0) ? chain    : 1;
    parallel_ = (parallel > 0) ? parallel : 1;
    return true;
  }

  // Rotating each tile swaps its w/h:
  // old_w = tile_w * chain, old_h = tile_h
  // => new_w = tile_h * chain, new_h = tile_w
  bool GetSizeMapping(int old_w, int old_h, int *new_w, int *new_h) const override {
    if (parallel_ != 1) return false;
    const int tile_w = old_w / chain_;   // e.g. 64
    const int tile_h = old_h;            // e.g. 32
    if (tile_w <= 0 || tile_h <= 0) return false;
    *new_w = tile_h * chain_;            // 32 * 8 = 256
    *new_h = tile_w;                     // 64
    return true;
  }

  // Map (x,y) in the rotated horizontal chain back to original unrotated chain.
  void MapVisibleToMatrix(int old_w, int old_h, int x, int y, int *ox, int *oy) const override {
    const int tile_w = old_w / chain_;   // 64
    const int tile_h = old_h;            // 32
    if (tile_w <= 0 || tile_h <= 0) { *ox = *oy = -1; return; }

    // After rotation, each tile is width=tile_h and height=tile_w, still laid out horizontally.
    const int panel      = x / tile_h;         // which tile (0..chain-1)
    const int x_in_panel = x % tile_h;         // 0..tile_h-1 (0..31)
    const int y_in_panel = y;                  // 0..tile_w-1 (0..63)

    // CCW appearance -> feed original with CW inverse: (u,v) = (tile_w - 1 - y', x')
    *ox = panel * tile_w + (tile_w - 1 - y_in_panel);
    *oy = x_in_panel;
  }

 private:
  int chain_, parallel_;
};

// auto-register so you can use --led-pixel-mapper=Tile90CCW:...
static struct _Reg {
  _Reg() { RegisterPixelMapper(new Tile90CCW()); }
} _reg_tile90ccw;
