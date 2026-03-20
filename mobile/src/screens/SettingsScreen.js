import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, Switch, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../services/api';

const LANGS = [{ code:'en', label:'English' },{ code:'es', label:'Español' },{ code:'hi', label:'हिन्दी' },{ code:'sw', label:'Kiswahili' }];
const TABS = ['Profile','Preferences','Security'];

export default function SettingsScreen() {
  const { user, logout, refreshUser } = useAuth(); const { theme, isDark, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [tab, setTab] = useState(0); const [saving, setSaving] = useState(false);
  const [name, setName] = useState(user?.name||''); const [phone, setPhone] = useState(user?.phone||'');
  const [location, setLocation] = useState(user?.location||''); const [farmName, setFarmName] = useState(''); const [farmSize, setFarmSize] = useState('');
  const [curPw, setCurPw] = useState(''); const [newPw, setNewPw] = useState(''); const [confPw, setConfPw] = useState('');

  useEffect(() => { (async () => { try { const d = await api.getMe(); const u = d.user; setName(u.name||''); setPhone(u.phone||''); setLocation(u.location||''); setFarmName(u.farm_name||''); setFarmSize(u.farm_size||''); } catch(e){} })(); }, []);

  async function saveProfile() { setSaving(true); try { await api.updateProfile({ name, phone, location, farm_name:farmName, farm_size:farmSize }); await refreshUser(); Alert.alert(t('common.success'), 'Profile updated'); } catch(e) { Alert.alert(t('common.error'), e.message); } finally { setSaving(false); } }
  async function changePw() { if (!curPw||!newPw||!confPw) { Alert.alert(t('common.error'), 'All fields required'); return; } setSaving(true); try { await api.changePassword(curPw, newPw, confPw); setCurPw(''); setNewPw(''); setConfPw(''); Alert.alert(t('common.success'), 'Password changed'); } catch(e) { Alert.alert(t('common.error'), e.message); } finally { setSaving(false); } }

  const Inp = (label, val, set, opts={}) => <View style={{ marginBottom:14 }}><Text style={{ color:theme.textSecondary, fontSize:13, fontWeight:'600', marginBottom:6 }}>{label}</Text><TextInput style={[s.input, { borderColor:theme.border, backgroundColor:theme.background, color:theme.text }]} value={val} onChangeText={set} placeholderTextColor={theme.textSecondary} {...opts} /></View>;

  return (
    <ScrollView style={[s.c, { backgroundColor: theme.background }]} keyboardShouldPersistTaps="handled">
      <Text style={[s.title, { color: theme.text }]}>{t('settings.title')}</Text>
      <View style={s.tabRow}>{TABS.map((tn,i) => <TouchableOpacity key={tn} style={[s.tab, { borderBottomColor:tab===i?theme.primary:'transparent' }]} onPress={() => setTab(i)}><Text style={{ color:tab===i?theme.primary:theme.textSecondary, fontSize:14, fontWeight:'700' }}>{tn}</Text></TouchableOpacity>)}</View>
      <View style={[s.card, { backgroundColor:theme.card, borderColor:theme.border }]}>
        {tab===0 && <>{Inp(t('settings.fullName'),name,setName)}{Inp(t('settings.email'),user?.email||'',()=>{},{editable:false})}{Inp(t('settings.phone'),phone,setPhone,{keyboardType:'phone-pad'})}{Inp(t('settings.location'),location,setLocation)}{Inp(t('settings.farmName'),farmName,setFarmName)}{Inp(t('settings.farmSize'),farmSize,setFarmSize,{keyboardType:'numeric'})}<TouchableOpacity style={[s.saveBtn, { backgroundColor:theme.primary }]} onPress={saveProfile} disabled={saving}>{saving ? <ActivityIndicator color="#fff" /> : <Text style={s.saveBtnText}>{t('settings.save')}</Text>}</TouchableOpacity></>}
        {tab===1 && <><View style={{ flexDirection:'row', justifyContent:'space-between', alignItems:'center' }}><View><Text style={{ color:theme.text, fontSize:15, fontWeight:'700' }}>{isDark ? t('settings.darkMode') : t('settings.lightMode')}</Text><Text style={{ color:theme.textSecondary, fontSize:12, marginTop:2 }}>Toggle dark/light appearance</Text></View><Switch value={isDark} onValueChange={toggleTheme} trackColor={{ true:theme.primary }} /></View><Text style={{ color:theme.text, fontSize:15, fontWeight:'700', marginTop:20 }}>{t('settings.language')}</Text><View style={{ flexDirection:'row', flexWrap:'wrap', marginTop:10 }}>{LANGS.map(l => <TouchableOpacity key={l.code} style={[s.langBtn, { backgroundColor:language===l.code?theme.primary:theme.background, borderColor:language===l.code?theme.primary:theme.border }]} onPress={() => { setLanguage(l.code); api.updatePreferences({ language:l.code }).catch(()=>{}); }}><Text style={{ color:language===l.code?'#fff':theme.text, fontSize:14, fontWeight:'600' }}>{l.label}</Text></TouchableOpacity>)}</View></>}
        {tab===2 && <>{Inp(t('settings.currentPassword'),curPw,setCurPw,{secureTextEntry:true})}{Inp(t('settings.newPassword'),newPw,setNewPw,{secureTextEntry:true})}{Inp(t('settings.confirmPassword'),confPw,setConfPw,{secureTextEntry:true})}<TouchableOpacity style={[s.saveBtn, { backgroundColor:theme.primary }]} onPress={changePw} disabled={saving}>{saving ? <ActivityIndicator color="#fff" /> : <Text style={s.saveBtnText}>{t('settings.changePassword')}</Text>}</TouchableOpacity></>}
      </View>
      <TouchableOpacity style={[s.logoutBtn, { borderColor:theme.danger }]} onPress={logout}><Ionicons name="log-out-outline" size={20} color={theme.danger} /><Text style={{ color:theme.danger, fontSize:15, fontWeight:'700', marginLeft:8 }}>{t('nav.logout')}</Text></TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  c:{flex:1}, title:{fontSize:24,fontWeight:'700',padding:20,paddingBottom:0},
  tabRow:{flexDirection:'row',paddingHorizontal:20,marginTop:16,marginBottom:12}, tab:{flex:1,paddingBottom:10,borderBottomWidth:3,alignItems:'center'},
  card:{marginHorizontal:16,borderRadius:14,padding:20,borderWidth:1},
  input:{height:46,borderWidth:1,borderRadius:12,paddingHorizontal:14,fontSize:15},
  saveBtn:{height:48,borderRadius:12,alignItems:'center',justifyContent:'center',marginTop:8}, saveBtnText:{color:'#fff',fontSize:15,fontWeight:'700'},
  langBtn:{paddingHorizontal:20,paddingVertical:10,borderRadius:12,borderWidth:1,marginRight:8,marginBottom:8},
  logoutBtn:{flexDirection:'row',alignItems:'center',justifyContent:'center',height:48,borderRadius:12,borderWidth:2,margin:16,marginBottom:40},
});
