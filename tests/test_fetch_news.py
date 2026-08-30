import importlib.util, json, tempfile, unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('fetch_news',Path(__file__).parents[1]/'scripts/fetch_news.py');m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
class FetchTests(unittest.TestCase):
 def test_clean_text_removes_html_and_limits(self):
  self.assertEqual(m.clean_text('<b>安全</b> &amp; 明確'),'安全 & 明確');self.assertLessEqual(len(m.clean_text('あ'*300)),180)
 def test_rejects_dangerous_urls(self):
  self.assertFalse(m.valid_url('javascript:alert(1)'));self.assertFalse(m.valid_url('data:text/html,x'));self.assertTrue(m.valid_url('https://example.org/a'))
 def test_clickbait_is_filtered_and_ai_flag_false(self):
  cfg={'excludeKeywords':['衝撃'],'categoryKeywords':{}};source={'name':'試験','category':'日本','sourceType':'test','language':'ja','priority':50}
  xml='''<rss><channel><item><title>衝撃の話</title><link>https://example.org/1</link></item><item><title>制度の変更</title><link>https://example.org/2</link><description><![CDATA[<script>x</script>暮らしに関係する説明です。詳しい内容を確認できます。]]></description></item></channel></rss>'''.encode()
  items=m.parse_feed(xml,source,cfg,m.datetime.now(m.timezone.utc));self.assertEqual(len(items),1);self.assertFalse(items[0]['aiGenerated']);self.assertNotIn('<script>',items[0]['summary'])
 def test_deduplicates_similar_titles(self):
  base={'importance':80,'publishedAt':'2026-01-01','url':'https://a.example/1','_fingerprint':'制度変更について','duplicateGroup':None}
  items=m.deduplicate([dict(base),{**base,'url':'https://b.example/2','_fingerprint':'制度変更について'}]);self.assertEqual(len(items),1);self.assertTrue(items[0]['duplicateGroup'])
 def test_balanced_top_three(self):
  cfg={'limits':{'top':3,'total':5,'perCategory':2,'goodNews':1},'categories':['日本','世界','韓国']};items=[]
  for i,c in enumerate(['日本','日本','世界','韓国','日本']):items.append({'id':i,'category':c})
  result=m.select_balanced(items,cfg);self.assertEqual(len({x['category'] for x in result[:3]}),3);self.assertLessEqual(len(result),5)
if __name__=='__main__':unittest.main()
