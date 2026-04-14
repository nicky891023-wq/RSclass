# 中文字體修復腳本
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

# 檢查系統可用字體
print("🔍 檢查系統可用中文字體...")
all_fonts = [f.name for f in fm.fontManager.ttflist]
chinese_fonts = [f for f in all_fonts if any(word in f for word in ['JhengHei', 'SimHei', 'Microsoft', 'Ming', 'Kai', 'FangSong', 'Noto', 'Source'])]

print(f"找到 {len(chinese_fonts)} 個可能的中文字體:")
for font in list(set(chinese_fonts))[:10]:
    print(f"   • {font}")

# 設置最佳字體
if 'Microsoft JhengHei' in chinese_fonts:
    best_font = 'Microsoft JhengHei'
elif 'SimHei' in chinese_fonts:
    best_font = 'SimHei'
elif 'Noto Sans CJK' in chinese_fonts:
    best_font = 'Noto Sans CJK'
elif 'Source Han Sans' in chinese_fonts:
    best_font = 'Source Han Sans'
else:
    best_font = chinese_fonts[0] if chinese_fonts else 'DejaVu Sans'

print(f"\n✅ 選擇最佳字體: {best_font}")

# 設置 matplotlib 字體
plt.rcParams['font.sans-serif'] = [best_font] + plt.rcParams['font.sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 測試中文顯示
print("\n🧪 測試中文顯示:")
try:
    fig, ax = plt.subplots(figsize=(8, 2))
    ax.text(0.5, 0.5, '中文測試 - 測試成功', 
            fontsize=16, ha='center', va='center', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.title('字體測試', fontsize=14)
    plt.tight_layout()
    plt.savefig('font_test.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("✅ 字體測試成功！")
except Exception as e:
    print(f"❌ 字體測試失敗: {e}")

print(f"\n📋 請在您的 Jupyter Notebook 中添加以下代碼:")
print(f"```python")
print(f"import matplotlib.pyplot as plt")
print(f"import matplotlib.font_manager as fm")
print(f"")
print(f"# 設置中文字體")
print(f"plt.rcParams['font.sans-serif'] = ['{best_font}', 'SimHei', 'Microsoft JhengHei', 'Arial Unicode MS']")
print(f"plt.rcParams['axes.unicode_minus'] = False")
print(f"```")
