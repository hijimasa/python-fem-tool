import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from datetime import datetime
import io
import base64
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os

class DocumentExporter:
    """解析結果をドキュメントとして出力するクラス"""
    
    def __init__(self, project_data):
        self.project_data = project_data
        self.styles = getSampleStyleSheet()
        
        # 日本語フォントの設定（システムにインストールされている場合）
        try:
            # Linuxの場合のフォントパス例
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    break
        except:
            pass
    
    def create_mesh_visualization(self, nodes, elements, title="メッシュ表示"):
        """メッシュの3D可視化画像を生成"""
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # メッシュの描画
        for elem in elements:
            tetra = nodes[elem]
            verts = [
                [tetra[0], tetra[1], tetra[2]],
                [tetra[0], tetra[1], tetra[3]],
                [tetra[0], tetra[2], tetra[3]],
                [tetra[1], tetra[2], tetra[3]]
            ]
            ax.add_collection3d(Poly3DCollection(verts, edgecolor="k", alpha=0.1, facecolor='lightgray'))
        
        # 固定端ノードを赤で表示
        for node_id in self.project_data.fixed_nodes:
            if node_id < len(nodes):
                ax.scatter(nodes[node_id, 0], nodes[node_id, 1], nodes[node_id, 2], 
                          color="red", s=50, label="固定端" if node_id == self.project_data.fixed_nodes[0] else "")
        
        # 力点を緑で表示
        for force in self.project_data.applied_forces:
            node_id = force[0]
            if node_id < len(nodes):
                ax.scatter(nodes[node_id, 0], nodes[node_id, 1], nodes[node_id, 2], 
                          color="green", s=50, label="力点" if force == self.project_data.applied_forces[0] else "")
                
                # 力ベクトルを表示
                fx, fy, fz = force[1], force[2], force[3]
                ax.quiver(nodes[node_id, 0], nodes[node_id, 1], nodes[node_id, 2],
                         fx, fy, fz, color="green", length=0.1, normalize=True)
        
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_zlabel("Z [m]")
        ax.set_title(title)
        ax.legend()
        
        return fig
    
    def create_deformation_visualization(self, nodes, elements, displacement, scale=1000):
        """変形後の形状を可視化"""
        fig = Figure(figsize=(12, 8))
        
        # 元の形状と変形後の形状を並べて表示
        ax1 = fig.add_subplot(121, projection='3d')
        ax2 = fig.add_subplot(122, projection='3d')
        
        # 元の形状
        for elem in elements:
            tetra = nodes[elem]
            verts = [
                [tetra[0], tetra[1], tetra[2]],
                [tetra[0], tetra[1], tetra[3]],
                [tetra[0], tetra[2], tetra[3]],
                [tetra[1], tetra[2], tetra[3]]
            ]
            ax1.add_collection3d(Poly3DCollection(verts, edgecolor="k", alpha=0.1, facecolor='lightgray'))
        
        ax1.set_title("変形前")
        ax1.set_xlabel("X [m]")
        ax1.set_ylabel("Y [m]")
        ax1.set_zlabel("Z [m]")
        
        # 変形後の形状
        deformed_nodes = np.zeros_like(nodes)
        for i in range(len(nodes)):
            for j in range(3):
                deformed_nodes[i][j] = nodes[i][j] + scale * displacement[i][j]
        
        for elem in elements:
            tetra = deformed_nodes[elem]
            verts = [
                [tetra[0], tetra[1], tetra[2]],
                [tetra[0], tetra[1], tetra[3]],
                [tetra[0], tetra[2], tetra[3]],
                [tetra[1], tetra[2], tetra[3]]
            ]
            ax2.add_collection3d(Poly3DCollection(verts, edgecolor="b", alpha=0.1, facecolor='lightblue'))
        
        ax2.set_title(f"変形後 (×{scale})")
        ax2.set_xlabel("X [m]")
        ax2.set_ylabel("Y [m]")
        ax2.set_zlabel("Z [m]")
        
        return fig
    
    def figure_to_image_data(self, fig):
        """matplotlib figureを画像データに変換"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        return image_data
    
    def get_yield_strength(self):
        """材料の降伏応力を取得"""
        # ProjectDataまたはアプリケーションから降伏応力を取得
        if hasattr(self.project_data, 'yield_strength') and self.project_data.yield_strength:
            return self.project_data.yield_strength
        # デフォルト値（一般的な鋼材）
        return 250e6  # Pa
    
    def export_to_html(self, output_path):
        """HTML形式でレポートを出力"""
        yield_strength = self.get_yield_strength()
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FEM解析レポート - {self.project_data.project_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .parameters {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .results {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .image-container {{ text-align: center; margin: 20px 0; }}
                .image-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                .safety-ok {{ color: #27ae60; font-weight: bold; }}
                .safety-warning {{ color: #f39c12; font-weight: bold; }}
                .safety-danger {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>有限要素法解析レポート</h1>
                <h2>{self.project_data.project_name}</h2>
                <p>作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
            </div>
            
            <div class="section">
                <h3>解析条件</h3>
                <div class="parameters">
                    <table>
                        <tr><th>項目</th><th>値</th><th>単位</th></tr>
                        <tr><td>ヤング率</td><td>{self.project_data.young_modulus:.2e}</td><td>Pa</td></tr>
                        <tr><td>ポアソン比</td><td>{self.project_data.poisson_ratio}</td><td>-</td></tr>
                        <tr><td>密度</td><td>{self.project_data.density}</td><td>kg/m³</td></tr>
                        <tr><td>降伏応力</td><td>{yield_strength:.2e}</td><td>Pa</td></tr>
                        <tr><td>重力考慮</td><td>{'有' if self.project_data.gravity_enabled else '無'}</td><td>-</td></tr>
                        <tr><td>固定端数</td><td>{len(self.project_data.fixed_nodes)}</td><td>個</td></tr>
                        <tr><td>荷重点数</td><td>{len(self.project_data.applied_forces)}</td><td>個</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h3>荷重条件</h3>
                <table>
                    <tr><th>ノード番号</th><th>X方向力[N]</th><th>Y方向力[N]</th><th>Z方向力[N]</th></tr>
        """
        
        for force in self.project_data.applied_forces:
            html_content += f"<tr><td>{force[0]}</td><td>{force[1]:.2f}</td><td>{force[2]:.2f}</td><td>{force[3]:.2f}</td></tr>"
        
        html_content += """
                </table>
            </div>
        """
        
        if self.project_data.displacement is not None:
            html_content += f"""
            <div class="section">
                <h3>解析結果</h3>
                <div class="results">
                    <table>
                        <tr><th>項目</th><th>値</th><th>単位</th></tr>
                        <tr><td>最大変位</td><td>{self.project_data.max_displacement:.6f}</td><td>m</td></tr>
            """
            
            if self.project_data.max_stress:
                html_content += f"""
                        <tr><td>最大応力</td><td>{self.project_data.max_stress:.2e}</td><td>Pa</td></tr>
                """
                
            if self.project_data.safety_factor:
                safety_class = "safety-ok" if self.project_data.safety_factor >= 2.0 else ("safety-warning" if self.project_data.safety_factor >= 1.5 else "safety-danger")
                safety_status = "安全" if self.project_data.safety_factor >= 2.0 else ("注意" if self.project_data.safety_factor >= 1.5 else "危険")
                html_content += f"""
                        <tr><td>安全率</td><td><span class="{safety_class}">{self.project_data.safety_factor:.2f} ({safety_status})</span></td><td>-</td></tr>
                """
                
            html_content += """
                    </table>
                </div>
            </div>
            """
        
        html_content += """
            <div class="section">
                <h3>図表</h3>
                <p>解析で使用したメッシュと境界条件を以下に示します。</p>
                <div class="image-container">
                    <p><em>注：この位置に3D可視化画像が表示されます</em></p>
                </div>
            </div>
            
            <div class="section">
                <h3>考察</h3>
                <p>この解析結果に基づいて、以下の点を検討することを推奨します：</p>
                <ul>
                    <li>最大応力の発生位置と設計への影響</li>
                    <li>安全率が適切な範囲にあるかの確認（推奨：2.0以上）</li>
                    <li>変形量が許容値以下であることの確認</li>
                </ul>
                <h4>安全率の評価基準</h4>
                <ul>
                    <li><span class="safety-ok">2.0以上：安全</span> - 通常の設計条件下で十分な安全性</li>
                    <li><span class="safety-warning">1.5以上2.0未満：注意</span> - 条件によっては危険、設計見直しを推奨</li>
                    <li><span class="safety-danger">1.5未満：危険</span> - 破損の可能性が高い、緊急に設計変更が必要</li>
                </ul>
            </div>
            
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def export_to_pdf(self, output_path):
        """PDF形式でレポートを出力"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # タイトル
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # center
        )
        
        story.append(Paragraph("有限要素法解析レポート", title_style))
        story.append(Paragraph(f"プロジェクト: {self.project_data.project_name}", self.styles['Heading2']))
        story.append(Paragraph(f"作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # 解析条件
        story.append(Paragraph("解析条件", self.styles['Heading2']))
        
        yield_strength = self.get_yield_strength()
        condition_data = [
            ['項目', '値', '単位'],
            ['ヤング率', f"{self.project_data.young_modulus:.2e}", 'Pa'],
            ['ポアソン比', f"{self.project_data.poisson_ratio}", '-'],
            ['密度', f"{self.project_data.density}", 'kg/m³'],
            ['降伏応力', f"{yield_strength:.2e}", 'Pa'],
            ['重力考慮', '有' if self.project_data.gravity_enabled else '無', '-'],
            ['固定端数', f"{len(self.project_data.fixed_nodes)}", '個'],
            ['荷重点数', f"{len(self.project_data.applied_forces)}", '個']
        ]
        
        condition_table = Table(condition_data)
        condition_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(condition_table)
        story.append(Spacer(1, 20))
        
        # 解析結果
        if self.project_data.displacement is not None:
            story.append(Paragraph("解析結果", self.styles['Heading2']))
            
            result_data = [['項目', '値', '単位']]
            result_data.append(['最大変位', f"{self.project_data.max_displacement:.6f}", 'm'])
            
            if self.project_data.max_stress:
                result_data.append(['最大応力', f"{self.project_data.max_stress:.2e}", 'Pa'])
            if self.project_data.safety_factor:
                safety_status = "安全" if self.project_data.safety_factor >= 2.0 else ("注意" if self.project_data.safety_factor >= 1.5 else "危険")
                result_data.append(['安全率', f"{self.project_data.safety_factor:.2f} ({safety_status})", '-'])
            
            result_table = Table(result_data)
            result_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(result_table)
        
        doc.build(story)
    
    def export_images(self, output_dir):
        """解析結果の画像を個別に出力"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        if self.project_data.nodes is not None and self.project_data.elements is not None:
            # メッシュ画像
            mesh_fig = self.create_mesh_visualization(self.project_data.nodes, self.project_data.elements)
            mesh_fig.savefig(os.path.join(output_dir, "mesh_visualization.png"), dpi=300, bbox_inches='tight')
            
            # 変形画像
            if self.project_data.displacement is not None:
                deform_fig = self.create_deformation_visualization(
                    self.project_data.nodes, 
                    self.project_data.elements, 
                    self.project_data.displacement,
                    self.project_data.display_scale
                )
                deform_fig.savefig(os.path.join(output_dir, "deformation_comparison.png"), dpi=300, bbox_inches='tight')