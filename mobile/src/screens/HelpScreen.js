import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';

function FAQ({ q, a, theme }) {
  const [open, setOpen] = useState(false);
  return (
    <TouchableOpacity style={[s.faq, { backgroundColor:theme.card, borderColor:theme.border }]} onPress={() => setOpen(!open)} activeOpacity={0.7}>
      <View style={s.faqHead}><Text style={[s.faqQ, { color:theme.text }]}>{q}</Text><Ionicons name={open?'chevron-up':'chevron-down'} size={20} color={theme.textSecondary} /></View>
      {open ? <Text style={{ color:theme.textSecondary, fontSize:13, marginTop:10, lineHeight:20 }}>{a}</Text> : null}
    </TouchableOpacity>
  );
}

export default function HelpScreen() {
  const { theme } = useTheme(); const { t } = useLanguage();
  const steps = [{ icon:'camera', title:t('help.step1Title'), desc:t('help.step1Desc'), color:theme.primary },{ icon:'analytics', title:t('help.step2Title'), desc:t('help.step2Desc'), color:theme.info },{ icon:'medkit', title:t('help.step3Title'), desc:t('help.step3Desc'), color:theme.success }];
  const faqs = [{ q:t('help.faq1Q'), a:t('help.faq1A') },{ q:t('help.faq2Q'), a:t('help.faq2A') },{ q:t('help.faq3Q'), a:t('help.faq3A') },{ q:t('help.faq4Q'), a:t('help.faq4A') },{ q:t('help.faq5Q'), a:t('help.faq5A') }];
  const tips = [t('help.tip1'),t('help.tip2'),t('help.tip3'),t('help.tip4'),t('help.tip5')];

  return (
    <ScrollView style={[s.c, { backgroundColor:theme.background }]} contentContainerStyle={{ padding:20, paddingBottom:40 }}>
      <Text style={[s.title, { color:theme.text }]}>{t('help.title')}</Text>
      <Text style={{ color:theme.textSecondary, fontSize:14, marginTop:4, marginBottom:20 }}>{t('help.subtitle')}</Text>
      <Text style={[s.sec, { color:theme.text }]}>{t('help.quickStart')}</Text>
      {steps.map((st,i) => <View key={i} style={[s.step, { backgroundColor:theme.card, borderColor:theme.border }]}><View style={[s.stepIcon, { backgroundColor:st.color+'20' }]}><Ionicons name={st.icon} size={24} color={st.color} /></View><View style={{ flex:1 }}><Text style={{ color:theme.text, fontSize:15, fontWeight:'700' }}>Step {i+1}: {st.title}</Text><Text style={{ color:theme.textSecondary, fontSize:13, marginTop:4, lineHeight:19 }}>{st.desc}</Text></View></View>)}
      <Text style={[s.sec, { color:theme.text }]}>{t('help.faq')}</Text>
      {faqs.map((f,i) => <FAQ key={i} q={f.q} a={f.a} theme={theme} />)}
      <Text style={[s.sec, { color:theme.text }]}>{t('help.tips')}</Text>
      <View style={[s.tipsCard, { backgroundColor:theme.primary+'10', borderColor:theme.primary+'30' }]}>{tips.map((tip,i) => <View key={i} style={{ flexDirection:'row', alignItems:'flex-start', marginBottom:10 }}><Ionicons name="bulb" size={16} color={theme.primary} /><Text style={{ color:theme.text, fontSize:13, marginLeft:10, flex:1, lineHeight:19 }}>{tip}</Text></View>)}</View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  c:{flex:1}, title:{fontSize:24,fontWeight:'700'}, sec:{fontSize:18,fontWeight:'700',marginTop:20,marginBottom:12},
  step:{flexDirection:'row',padding:16,borderRadius:14,borderWidth:1,marginBottom:10,alignItems:'center'}, stepIcon:{width:48,height:48,borderRadius:14,alignItems:'center',justifyContent:'center',marginRight:14},
  faq:{borderRadius:12,borderWidth:1,padding:16,marginBottom:8}, faqHead:{flexDirection:'row',justifyContent:'space-between',alignItems:'center'}, faqQ:{fontSize:14,fontWeight:'700',flex:1,marginRight:8},
  tipsCard:{borderRadius:14,borderWidth:1,padding:16},
});
