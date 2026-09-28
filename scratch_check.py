import os
import sys

def apply_updates():
    targets = [
        r"c:\Users\deeks\OneDrive\Desktop\SIH\index.html",
        r"c:\Users\deeks\OneDrive\Desktop\SIH\frontend\index.html"
    ]

    for target_path in targets:
        print(f"Processing: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Update EVENT_COLORS if missing uppercase keys
        if "'INDUSTRIAL_FIRE':" not in content:
            old_colors = """    'Unknown':                    { hex:'#7A8699', cls:'risk-low',        clsShort:'low'        }
  };"""
            new_colors = """    'Unknown':                    { hex:'#7A8699', cls:'risk-low',        clsShort:'low'        },
    'INDUSTRIAL_FIRE':                     { hex:'#DC2626', cls:'risk-critical',   clsShort:'critical'   },
    'FOREST_OR_WILDFIRE':                  { hex:'#EA580C', cls:'risk-high',       clsShort:'high'       },
    'AGRICULTURAL_BURNING':                { hex:'#16A34A', cls:'risk-low',        clsShort:'low'        },
    'GAS_FLARE':                           { hex:'#CA8A04', cls:'risk-gas',        clsShort:'gas'        },
    'MINING_THERMAL_ACTIVITY':             { hex:'#D97706', cls:'risk-gas',        clsShort:'gas'        },
    'PERSISTENT_INDUSTRIAL_THERMAL_SOURCE':{ hex:'#7C3AED', cls:'risk-persistent', clsShort:'persistent'},
    'OTHER_THERMAL_EVENT':                 { hex:'#64748B', cls:'risk-low',        clsShort:'low'        }
  };"""
            assert old_colors in content, f"Could not find old_colors in {target_path}"
            content = content.replace(old_colors, new_colors, 1)

        print(f"  [OK] EVENT_COLORS checked for {target_path}")

    print("Pre-checks completed.")

if __name__ == "__main__":
    apply_updates()
