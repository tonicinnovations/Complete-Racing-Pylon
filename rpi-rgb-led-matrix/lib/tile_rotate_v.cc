// tile_rotate_v.cc — per-panel 90° rotate before vertical stacking
#include <string>
#include <algorithm>
#include <cctype>
#include "pixel-mapper.h"

using namespace rgb_matrix;

class TileRotateVMapper : public PixelMapper {
 public:
  TileRotateVMapper()
      : chain_(1), parallel_(1),
        rotate_ccw_(true), flip_stack_(false) {}

  // Match your pixel-mapper.h
  const char *GetName() const override { return "TileRotateV"; }

  // Params: "ccw" (default) or "cw", optional "flip"
  // Examples:
  //   TileRotateV:8:1,ccw
  //   TileRotateV:8:1,cw,flip
  bool SetParameters(int chain, int parallel, const char *param) override {
    chain_    = (chain   > 0) ? chain   : 1;
    parallel_ = (parallel> 0) ? parallel: 1;   // this mapper assumes parallel == 1

    rotate_ccw_ = true;
    flip_stack_ = false;

    if (param && *param) {
      std::string p(param);
      std::transform(p.begin(), p.end(), p.begin(),
                     [](unsigned char c){ return std::tolower(c); });
      if (p.find("cw")   != std::string::npos) rotate_ccw_ = false;
      if (p.find("flip") != std::string::npos) flip_stack_ = true;
    }
    return true;  // parameters accepted
  }

  // Turn a horizontal chain (old_w = cols*chain) into one vertical column
  bool GetSizeMapping(int old_w, int old_h,
                      int *new_w, int *new_h) const override {
    if (parallel_ != 1) return false;           // keep simple for your setup
    const int tile_w = old_w / chain_;
    if (tile_w <= 0) return false;
    *new_w = tile_w;          // 64 (typical)
    *new_h = old_h * chain_;  // 32 * 8 = 256 (typical)
    return true;
  }

  // Map new visible (x,y) into original matrix coords (orig_x, orig_y)
  void MapVisibleToMatrix(int old_w, int old_h,
                          int x, int y,
                          int *orig_x, int *orig_y) const override {
    const int tile_w = old_w / chain_;   // 64
    const int tile_h = old_h;            // 32

    if (tile_w <= 0 || tile_h <= 0) { *orig_x = *orig_y = -1; return; }

    // Which tile down the column are we drawing to?
    int panel = y / tile_h;              // 0..chain_-1
    int y_in  = y % tile_h;              // 0..31
    int x_in  = x;                       // 0..63

    // Optional stack flip (top↔bottom)
    if (flip_stack_) panel = (chain_ - 1) - panel;

    // We want the PANEL to APPEAR rotated 90°. Feed the underlying
    // unrotated tile with the inverse mapping.
    if (rotate_ccw_) {
      // CCW appearance -> inverse is CW:
      //   src_u = tile_w - 1 - y_in
      //   src_v = x_in
      *orig_x = panel * tile_w + (tile_w - 1 - y_in);
      *orig_y = x_in;
    } else {
      // CW appearance -> inverse is CCW:
      //   src_u = y_in
      //   src_v = tile_h - 1 - x_in
      *orig_x = panel * tile_w + y_in;
      *orig_y = tile_h - 1 - x_in;
    }
  }

 private:
  int  chain_, parallel_;
  bool rotate_ccw_;
  bool flip_stack_;
};

// Register automatically with the library so it shows up as --led-pixel-mapper=TileRotateV:...
static struct _RegisterTRV {
  _RegisterTRV() { RegisterPixelMapper(new TileRotateVMapper()); }
} _register_trv;
