import io, re
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='TikTok Shop | Đánh giá Creative Ngọc Mỹ Procare',page_icon='📊',layout='wide')
st.markdown('''<style>.block-container{padding-top:1.2rem;max-width:1500px}div[data-testid="stMetric"]{background:#f4f7fb;border:1px solid #e3eaf2;border-radius:12px;padding:13px}h1,h2,h3{color:#172b4d}div[data-testid="stSidebar"]{background:#f6f8fc}</style>''',unsafe_allow_html=True)
BASE=Path(__file__).parent
FILES={'Creative':'Creative data 2026-10-15 - 2026-10-29 - Product 0.xlsx','Product':'Product data 2026-10-15 - 2026-10-29.xlsx','Campaign':'Product campaign data 2026-10-15 - 2026-10-29.xlsx'}
@st.cache_data(show_spinner=False)
def read_xlsx(blob):return pd.read_excel(io.BytesIO(blob),dtype={'ID SPU':str,'ID sản phẩm':str,'ID bài đăng':str,'ID chiến dịch':str})
def num(s):return pd.to_numeric(s.astype(str).str.replace(',','',regex=False).str.replace('%','',regex=False).str.replace('−','-',regex=False).replace({'-':None,'N/A':None,'nan':None}),errors='coerce').fillna(0)
def safe(a,b):return a/b if b else 0.
def money(x):return f'{x:,.0f}đ'.replace(',','.')
def pct(x):return f'{x*100:.2f}%'.replace('.',',')
def fmt(x):return f'{x:.2f}'.replace('.',',')
def label(name):
 n=str(name).lower()
 for key,val in [('whitening bb','K3 Whitening BB Cream'),('a&d','Natureplex A&D'),('qderma plus','Qderma Plus'),('qderma 20','Qderma 20g'),('lalisse','Lalisse Scargel'),('white eva','NAS White Eva'),('ex-collagen','Ex-Collagen'),('aosa','K3 Aosa Cleanser'),('acne treatment','Acne Treatment'),('munspot','Munspot'),('rice bran','Rice Bran Clay Mask')]:
  if key in n:return val
 return str(name)[:65]
with st.sidebar:
 st.header('📁 Dữ liệu đầu vào')
 uploads={}
 for k in FILES:
  uploads[k]=st.file_uploader(f'{k} data (.xlsx)',type='xlsx',key=k)
 st.caption('Không tải file: sử dụng bộ dữ liệu mẫu 15–29/10/2026 được đóng gói cùng app.')
 st.divider()
 st.header('⚙️ Tiêu chí đánh giá')
 min_spend=st.number_input('Chi tiêu tối thiểu để đánh giá mẫu',min_value=0,value=100000,step=25000)
 min_click=st.number_input('Số nhấp tối thiểu',min_value=0,value=20,step=5)
 target=st.number_input('ROAS mục tiêu tham chiếu',min_value=0.1,value=3.0,step=.1)
 st.caption('ROAS mục tiêu chỉ dùng tham chiếu; mỗi sản phẩm có thể có ngưỡng riêng.')
 try:
  blobs={k:(uploads[k].getvalue() if uploads[k] else (BASE/FILES[k]).read_bytes()) for k in FILES}
 except FileNotFoundError:
  st.error('Chưa có file mẫu. Vui lòng tải lên đủ 3 file Excel.');st.stop()
try:
 c=read_xlsx(blobs['Creative']).copy(); p=read_xlsx(blobs['Product']).copy(); camp=read_xlsx(blobs['Campaign']).copy()
 required=['Tên sản phẩm','Loại nội dung sáng tạo','Chi phí','Doanh thu gộp','Số lượng đơn hàng SKU','Số lượt hiển thị quảng cáo sản phẩm','Số lượt nhấp vào quảng cáo sản phẩm']
 missing=[x for x in required if x not in c.columns]
 if missing:st.error('Thiếu cột Creative: '+', '.join(missing));st.stop()
except Exception as e:st.error(f'Không đọc được file: {e}');st.stop()
for k in ['Chi phí','Doanh thu gộp','Số lượng đơn hàng SKU','Số lượt hiển thị quảng cáo sản phẩm','Số lượt nhấp vào quảng cáo sản phẩm','Tỷ lệ xem video quảng cáo trong 2 giây','Tỷ lệ xem video quảng cáo trong 6 giây','Tỷ lệ xem 25% thời lượng video quảng cáo','Tỷ lệ xem 50% thời lượng video quảng cáo','Tỷ lệ xem 75% thời lượng video quảng cáo','Tỷ lệ xem 100% thời lượng video quảng cáo']:
 if k not in c:c[k]=0
 c[k]=num(c[k])
c['Loại']=c['Loại nội dung sáng tạo'].apply(lambda x:'Thẻ sản phẩm' if 'thẻ' in str(x).lower() else 'Video')
c['Sản phẩm']=c['Tên sản phẩm'].map(label)
c['ID mẫu']=c['ID bài đăng'].astype(str)
c['Tên mẫu']=c['Mẫu quảng cáo'].fillna('-').astype(str)
c['CTR']=np.where(c['Số lượt hiển thị quảng cáo sản phẩm']>0,c['Số lượt nhấp vào quảng cáo sản phẩm']/c['Số lượt hiển thị quảng cáo sản phẩm'],0)
c['CVR']=np.where(c['Số lượt nhấp vào quảng cáo sản phẩm']>0,c['Số lượng đơn hàng SKU']/c['Số lượt nhấp vào quảng cáo sản phẩm'],0)
c['ROAS']=np.where(c['Chi phí']>0,c['Doanh thu gộp']/c['Chi phí'],0)
# Important: rows with zero spend and attributed orders must be displayed but not ranked as paid performance.
c['Đủ mẫu']=(c['Chi phí']>=min_spend)&(c['Số lượt nhấp vào quảng cáo sản phẩm']>=min_click)
c['Cảnh báo']=np.where((c['Chi phí']==0)&(c['Số lượng đơn hàng SKU']>0),'Có đơn nhưng chi phí = 0; không xếp hạng ROAS','')
agg=c.groupby(['Sản phẩm','Loại'],as_index=False).agg(Chi_phi=('Chi phí','sum'),Doanh_thu=('Doanh thu gộp','sum'),Don=('Số lượng đơn hàng SKU','sum'),Hien_thi=('Số lượt hiển thị quảng cáo sản phẩm','sum'),Nhap=('Số lượt nhấp vào quảng cáo sản phẩm','sum'),Mau=('Loại','size'))
agg['ROAS']=np.where(agg.Chi_phi>0,agg.Doanh_thu/agg.Chi_phi,0)
agg['CTR']=np.where(agg.Hien_thi>0,agg.Nhap/agg.Hien_thi,0)
agg['CVR']=np.where(agg.Nhap>0,agg.Don/agg.Nhap,0)
products=sorted(c['Sản phẩm'].unique())
st.title('TikTok Shop | Đánh giá chất lượng Creative Ngọc Mỹ Procare')
st.caption('Tổng hợp theo sản phẩm • Thẻ sản phẩm và video • Chỉ số tính lại từ dữ liệu gốc, không lấy trung bình ROI/CTR/CVR từng dòng')
if uploads['Creative'] and (not uploads['Product'] or not uploads['Campaign']):st.info('Đang kết hợp file Creative mới với các file Product/Campaign mặc định. Hãy tải đồng bộ cả ba file nếu cần đối soát cùng kỳ.')
t1,t2,t3=st.tabs(['📊 1. Tổng quan','⚖️ 2. So sánh thẻ & video','🎬 3. Đánh giá từng sản phẩm'])
with t1:
 a,b,d,e=st.columns(4)
 a.metric('Sản phẩm',len(products));b.metric('Thẻ sản phẩm',int((c.Loại=='Thẻ sản phẩm').sum()));d.metric('Video',int((c.Loại=='Video').sum()));e.metric('Tổng mẫu',len(c))
 total_cost=c['Chi phí'].sum();total_rev=c['Doanh thu gộp'].sum();total_imp=c['Số lượt hiển thị quảng cáo sản phẩm'].sum();total_click=c['Số lượt nhấp vào quảng cáo sản phẩm'].sum();total_orders=c['Số lượng đơn hàng SKU'].sum()
 cols=st.columns(5)
 for col,title,value in zip(cols,['Chi phí','Doanh thu gộp','ROAS','CTR','CVR'],[money(total_cost),money(total_rev),fmt(safe(total_rev,total_cost)),pct(safe(total_click,total_imp)),pct(safe(total_orders,total_click))]):col.metric(title,value)
 st.info('CTR = nhấp / hiển thị; CVR = đơn SKU / nhấp; ROAS = doanh thu gộp / chi phí. CVR là tỷ lệ chuyển đổi theo đơn SKU, có thể khác tỷ lệ mua hàng thực tế nếu một lượt nhấp tạo nhiều SKU.')
 bytype=agg.groupby('Loại',as_index=False)[['Chi_phi','Doanh_thu','Don','Nhap','Hien_thi']].sum()
 l,r=st.columns(2)
 with l:st.plotly_chart(px.pie(bytype,names='Loại',values='Chi_phi',hole=.5,title='Tỷ trọng chi phí theo định dạng',color_discrete_sequence=['#1d70b8','#f5a524']),use_container_width=True)
 with r:st.plotly_chart(px.bar(agg.groupby('Sản phẩm',as_index=False)['Chi_phi'].sum().sort_values('Chi_phi',ascending=False),x='Sản phẩm',y='Chi_phi',title='Chi phí theo sản phẩm',color_discrete_sequence=['#2563eb']),use_container_width=True)
 st.dataframe(bytype.rename(columns={'Chi_phi':'Chi phí','Doanh_thu':'Doanh thu','Don':'Đơn SKU','Nhap':'Nhấp','Hien_thi':'Hiển thị'}),hide_index=True,use_container_width=True)
with t2:
 st.subheader('So sánh hiệu quả thẻ sản phẩm và video')
 st.caption('ROAS được tính lại bằng tổng doanh thu / tổng chi phí. CTR và CVR được tính theo tổng nhấp, tổng hiển thị và tổng đơn; không lấy trung bình các tỷ lệ.')
 metric=st.selectbox('Chỉ số biểu đồ',['ROAS','CTR','CVR','Chi_phi','Don'],format_func=lambda v:{'Chi_phi':'Chi phí','Don':'Số đơn SKU'}.get(v,v))
 fig=px.bar(agg,x='Sản phẩm',y=metric,color='Loại',barmode='group',color_discrete_map={'Thẻ sản phẩm':'#2563eb','Video':'#f59e0b'},hover_data=['Chi_phi','Doanh_thu','Don','Nhap','Hien_thi'],title='So sánh '+metric+' theo từng sản phẩm')
 if metric in ['CTR','CVR']:fig.update_yaxes(tickformat='.1%')
 fig.update_layout(xaxis_tickangle=-35,legend_title_text='Định dạng',height=480)
 st.plotly_chart(fig,use_container_width=True)
 rows=[]
 for name in products:
  rec={'Sản phẩm':name}
  for kind,short in [('Thẻ sản phẩm','Thẻ'),('Video','Video')]:
   q=agg[(agg['Sản phẩm']==name)&(agg['Loại']==kind)]
   if len(q):
    z=q.iloc[0];rec.update({f'ROAS {short}':round(z.ROAS,2),f'CTR {short}':pct(z.CTR),f'CVR {short}':pct(z.CVR),f'Chi phí {short}':int(z.Chi_phi),f'Đơn {short}':int(z.Don)})
   else:rec.update({f'ROAS {short}':None,f'CTR {short}':'—',f'CVR {short}':'—',f'Chi phí {short}':0,f'Đơn {short}':0})
  rows.append(rec)
 st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
 st.caption('Lưu ý: ROAS = 0 nếu không có doanh thu và có chi phí; mẫu có chi phí 0 không được diễn giải là ROAS 0 có ý nghĩa. Cần đối soát chênh lệch giữa file Creative và Product/Campaign.')
with t3:
 selected=st.selectbox('🔎 Chọn sản phẩm để đánh giá',products)
 sub=c[c['Sản phẩm']==selected].copy()
 st.subheader(selected)
 cols=st.columns(4)
 for col,title,value in zip(cols,['Tổng chi phí','Doanh thu','ROAS','Đơn SKU'],[money(sub['Chi phí'].sum()),money(sub['Doanh thu gộp'].sum()),fmt(safe(sub['Doanh thu gộp'].sum(),sub['Chi phí'].sum())),str(int(sub['Số lượng đơn hàng SKU'].sum()))]):col.metric(title,value)
 st.markdown('### A. Đánh giá từng thẻ sản phẩm')
 cards=sub[sub.Loại=='Thẻ sản phẩm']
 if cards.empty:st.info('Không có thẻ sản phẩm trong file Creative.')
 for i,(_,z) in enumerate(cards.iterrows(),1):
  with st.container(border=True):
   st.markdown(f'**Thẻ sản phẩm #{i}** — {money(z["Chi phí"])} | {int(z["Số lượng đơn hàng SKU"])} đơn | ROAS {fmt(z.ROAS)} | CTR {pct(z.CTR)} | CVR {pct(z.CVR)}')
   if z['Chi phí']==0:st.warning('Chưa có chi phí đủ để đánh giá hiệu quả.')
   elif z['Số lượng đơn hàng SKU']==0 and z['Chi phí']>=min_spend:st.error('Chưa tạo đơn dù đã tiêu ngân sách đáng kể. Ưu tiên giảm phân phối thẻ, kiểm tra ảnh bìa, giá, đánh giá và ưu đãi.')
   elif z['Số lượng đơn hàng SKU']==0:st.info('Chưa có đơn, nhưng chi phí còn nhỏ. Theo dõi thêm trước khi kết luận.')
   elif z.ROAS>=target and z['Số lượng đơn hàng SKU']>=3:st.success('Có tín hiệu hiệu quả và nhiều đơn. Giữ mẫu, kiểm chứng khả năng duy trì ROAS trước khi tăng ngân sách.')
   elif z.ROAS>=target:st.info('ROAS vượt mức tham chiếu nhưng số đơn còn ít. Giữ để kiểm chứng, không tăng ngân sách đột ngột.')
   else:st.warning('Đã tạo đơn nhưng ROAS dưới mức tham chiếu. Kiểm tra ảnh, giá, voucher và trang sản phẩm; hạn chế mở rộng ngân sách.')
 st.markdown('### B. Đánh giá chất lượng video')
 vids=sub[sub.Loại=='Video'].copy()
 if vids.empty:st.info('Không có video.')
 else:
  eligible=vids[(vids['Chi phí']>0)&vids['Đủ mẫu']].copy()
  eligible['Điểm']=eligible['ROAS']*0.7+eligible['CVR']*10*0.3
  good=eligible[eligible['Số lượng đơn hàng SKU']>0].sort_values(['ROAS','Số lượng đơn hàng SKU'],ascending=False).head(5)
  bad=eligible[(eligible['Số lượng đơn hàng SKU']==0)|(eligible['ROAS']<1)].sort_values(['Chi phí','ROAS'],ascending=[False,True]).head(5)
  x,y=st.columns(2)
  def video_table(df):
   if df.empty:return pd.DataFrame()
   o=df[['ID mẫu','Tên mẫu','Chi phí','Số lượng đơn hàng SKU','ROAS','CTR','CVR']].copy();o['Tên mẫu']=o['Tên mẫu'].str.slice(0,75)
   for k in ['CTR','CVR']:o[k]=o[k].map(pct)
   return o.rename(columns={'Chi phí':'Chi phí (đ)','Số lượng đơn hàng SKU':'Đơn SKU','Tên mẫu':'Nội dung'})
  with x:
   st.markdown('#### 🟢 Top video có tín hiệu tốt')
   if good.empty:st.info('Chưa có video đủ mẫu và có đơn để xếp hạng.')
   else:st.dataframe(video_table(good),hide_index=True,use_container_width=True);st.caption('Ưu tiên nhân bản ý tưởng/hook và kiểm chứng bằng video mới; không sao chép nguyên mẫu một cách máy móc.')
  with y:
   st.markdown('#### 🔴 Top video cần thay thế / rà soát')
   if bad.empty:st.info('Chưa có video đủ điều kiện xác định hiệu quả kém.')
   else:st.dataframe(video_table(bad),hide_index=True,use_container_width=True);st.caption('Xem xét giảm phân phối mẫu tiêu nhiều nhưng không ra đơn; việc tắt creative phụ thuộc cơ chế GMV Max.')
  st.markdown('### C. Phân tích một video cụ thể')
  vids=vids.reset_index(drop=True)
  vids['Lựa chọn']=vids.apply(lambda z:f'{str(z["ID mẫu"])} | {z["Tên mẫu"][:90]}',axis=1)
  chosen=st.selectbox('🎞️ Chọn video',vids.index,format_func=lambda i:vids.loc[i,'Lựa chọn'])
  z=vids.loc[chosen]
  st.write('**Tên/video caption:**',z['Tên mẫu']);st.caption('ID bài đăng: '+z['ID mẫu'])
  cc=st.columns(6)
  for col,ttl,val in zip(cc,['Chi phí','Doanh thu','Đơn','ROAS','CTR','CVR'],[money(z['Chi phí']),money(z['Doanh thu gộp']),str(int(z['Số lượng đơn hàng SKU'])),fmt(z.ROAS),pct(z.CTR),pct(z.CVR)]):col.metric(ttl,val)
  retention=[('Xem 2 giây','Tỷ lệ xem video quảng cáo trong 2 giây'),('Xem 6 giây','Tỷ lệ xem video quảng cáo trong 6 giây'),('Xem 25%','Tỷ lệ xem 25% thời lượng video quảng cáo'),('Xem 50%','Tỷ lệ xem 50% thời lượng video quảng cáo'),('Xem 75%','Tỷ lệ xem 75% thời lượng video quảng cáo'),('Xem 100%','Tỷ lệ xem 100% thời lượng video quảng cáo')]
  if z['Chi phí']>0 and any(z[k]>0 for _,k in retention):
   ret=pd.DataFrame({'Mốc':[a for a,k in retention],'Tỷ lệ':[float(z[k]) for a,k in retention]})
   st.plotly_chart(px.bar(ret,x='Mốc',y='Tỷ lệ',title='Giữ chân người xem qua các mốc',text=ret['Tỷ lệ'].map(pct),color_discrete_sequence=['#0ea5e9']).update_yaxes(tickformat='.0%'),use_container_width=True)
  strengths=[];weaknesses=[];actions=[]
  ref=vids[(vids['Chi phí']>0)&(vids['Số lượt hiển thị quảng cáo sản phẩm']>0)]
  baseline_ctr=safe(ref['Số lượt nhấp vào quảng cáo sản phẩm'].sum(),ref['Số lượt hiển thị quảng cáo sản phẩm'].sum())
  baseline_cvr=safe(ref['Số lượng đơn hàng SKU'].sum(),ref['Số lượt nhấp vào quảng cáo sản phẩm'].sum())
  if z['Chi phí']==0:
   weaknesses.append('Không có chi tiêu quảng cáo; dữ liệu hiện tại không đủ để chấm chất lượng mẫu.')
  else:
   if z['Số lượt hiển thị quảng cáo sản phẩm']>=500:
    if z.CTR>=baseline_ctr:strengths.append(f'CTR {pct(z.CTR)} cao hơn hoặc bằng CTR video của sản phẩm ({pct(baseline_ctr)}): có tín hiệu thu hút nhấp tốt.')
    else:weaknesses.append(f'CTR {pct(z.CTR)} thấp hơn mức video cùng sản phẩm ({pct(baseline_ctr)}): hook, thumbnail hoặc lời kêu gọi nhấp chưa hấp dẫn.');actions.append('Thử 2–3 hook đầu video, thay cảnh mở đầu và đưa lợi ích chính lên sớm.')
   if z['Số lượt nhấp vào quảng cáo sản phẩm']>=min_click:
    if z.CVR>=baseline_cvr and z['Số lượng đơn hàng SKU']>0:strengths.append(f'CVR {pct(z.CVR)} không thấp hơn mức video cùng sản phẩm ({pct(baseline_cvr)}).')
    else:weaknesses.append(f'CVR {pct(z.CVR)} thấp hơn mức tham chiếu nội bộ ({pct(baseline_cvr)}): người nhấp chưa mua tương xứng.');actions.append('Kiểm tra thông điệp so với trang sản phẩm, giá, ưu đãi, đánh giá và CTA; tránh hứa hẹn quá mức.')
   if z['Số lượng đơn hàng SKU']>0:strengths.append(f'Có {int(z["Số lượng đơn hàng SKU"])} đơn SKU được ghi nhận.')
   elif z['Chi phí']>=min_spend:weaknesses.append('Đã chi đáng kể nhưng chưa có đơn.');actions.append('Ưu tiên thử creative mới và giảm ưu tiên mẫu này nếu kết quả tiếp tục kém.')
   if z.ROAS>=target and z['Số lượng đơn hàng SKU']>=2:strengths.append(f'ROAS {fmt(z.ROAS)} đạt ngưỡng tham chiếu với ít nhất 2 đơn; có thể thử nhân bản góc nội dung.')
   elif z['Số lượng đơn hàng SKU']>0 and z.ROAS<target:weaknesses.append(f'ROAS {fmt(z.ROAS)} chưa đạt ngưỡng tham chiếu {fmt(target)}.')
   if z['Tỷ lệ xem video quảng cáo trong 2 giây']>0:
    if z['Tỷ lệ xem video quảng cáo trong 2 giây']<.35:weaknesses.append('Tỷ lệ xem 2 giây thấp: khả năng giữ người xem ở phần mở đầu còn yếu.');actions.append('Đưa tình huống/vấn đề khách hàng và hình ảnh sản phẩm vào 2 giây đầu.')
    else:strengths.append('Có tín hiệu giữ người xem trong 2 giây đầu; cần so sánh với video cùng sản phẩm để kết luận chắc hơn.')
   if z['Tỷ lệ xem video quảng cáo trong 6 giây']>0 and z['Tỷ lệ xem video quảng cáo trong 2 giây']>0 and z['Tỷ lệ xem video quảng cáo trong 6 giây'] < z['Tỷ lệ xem video quảng cáo trong 2 giây']*.4:
    weaknesses.append('Tỷ lệ xem 6 giây giảm mạnh so với 2 giây: nội dung giữa đoạn mở đầu chưa đủ giữ chân.');actions.append('Rút ngắn lời dẫn, tăng cảnh minh họa/demonstration, cho thấy lợi ích sớm hơn.')
  if not strengths:strengths=['Chưa có tín hiệu đủ mạnh để xác nhận điểm tốt từ dữ liệu hiện có.']
  if not weaknesses:weaknesses=['Chưa phát hiện điểm yếu rõ ràng theo các ngưỡng định lượng đang chọn; cần xem trực tiếp video.']
  if not actions:actions=['Giữ theo dõi, kiểm chứng với thêm nhấp/đơn và xem nội dung thực tế trước khi quyết định.']
  left,right=st.columns(2)
  with left:st.success('**Điểm đang làm tốt**\n\n'+'\n\n'.join('• '+a for a in strengths))
  with right:st.warning('**Điểm cần cải thiện**\n\n'+'\n\n'.join('• '+a for a in weaknesses))
  st.info('**Hành động đề xuất**\n\n'+'\n\n'.join('• '+a for a in dict.fromkeys(actions)))
  if not bool(z['Đủ mẫu']):st.caption('⚠️ Chưa đạt đồng thời ngưỡng chi phí và nhấp đã chọn; nhận định chỉ mang tính thăm dò.')
  if z['Cảnh báo']:st.warning(z['Cảnh báo'])
  st.caption('Đây là chẩn đoán từ chỉ số phân phối và caption, không phải đánh giá trực tiếp hình ảnh/âm thanh/kịch bản video. Cần xem video gốc để xác nhận nguyên nhân.')
  with st.expander('Xem toàn bộ video của sản phẩm'):
   st.dataframe(video_table(vids.sort_values('Chi phí',ascending=False)),hide_index=True,use_container_width=True)
st.divider()
st.caption('Dữ liệu Creative có thể chứa mẫu chi phí = 0 nhưng vẫn có đơn, hoặc tỷ lệ chuyển đổi do nền tảng cung cấp không trùng đơn SKU/nhấp. App chủ động tính lại từ tổng và không gộp chồng dữ liệu Product/Campaign vào Creative.')
