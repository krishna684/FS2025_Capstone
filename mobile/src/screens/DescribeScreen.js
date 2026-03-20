import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../services/api';

const PLANTS = ['Tomato','Corn','Soybean','Wheat','Rice','Cabbage','Lettuce','Bean','Rose','Other'];

export default function DescribeScreen({ navigation }) {
  const { theme } = useTheme(); const { t } = useLanguage();
  const [symptoms, setSymptoms] = useState(''); const [plantType, setPlantType] = useState(''); const [analyzing, setAnalyzing] = useState(false);

  async function handleAnalyze() {
    if (!symptoms.trim()) { Alert.alert(t('common.error'), 'Please describe the symptoms'); return; }
    setAnalyzing(true);
    try { const r = await api.analyzeSymptoms(symptoms, plantType); navigation.navigate('Results', { result: r, type: 'text' }); }
    catch (e) { Alert.alert(t('common.error'), e.message); } finally { setAnalyzing(false); }
  }

  return (
    <KeyboardAvoidingView style={[s.c, { backgroundColor: theme.background }]} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={{ padding: 20 }} keyboardShouldPersistTaps="handled">
        <Text style={[s.title, { color: theme.text }]}>Describe Symptoms</Text>
        <Text style={{ color: theme.textSecondary, fontSize: 14, marginTop: 4, marginBottom: 20 }}>Describe what you observe on your plant for AI analysis</Text>
        <Text style={[s.label, { color: theme.text }]}>Plant Type</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 4 }}>
          {PLANTS.map(p => <TouchableOpacity key={p} style={[s.chip, { borderColor: theme.border, backgroundColor: plantType===p ? theme.primary : theme.card }]} onPress={() => setPlantType(p)}><Text style={{ color: plantType===p ? '#fff' : theme.text, fontSize:13, fontWeight:'600' }}>{p}</Text></TouchableOpacity>)}
        </ScrollView>
        <Text style={[s.label, { color: theme.text, marginTop: 20 }]}>Symptoms</Text>
        <TextInput style={[s.textArea, { borderColor: theme.border, backgroundColor: theme.card, color: theme.text }]} placeholder="Describe what you see..." placeholderTextColor={theme.textSecondary} value={symptoms} onChangeText={setSymptoms} multiline numberOfLines={6} textAlignVertical="top" />
        <View style={[s.tips, { backgroundColor: theme.primary+'10', borderColor: theme.primary+'30' }]}>
          <Text style={{ color: theme.primary, fontWeight:'700', marginBottom:8, fontSize:14 }}>Tips for better results:</Text>
          {['Describe the color and pattern of damage','Mention any visible insects or webs','Note which part of the plant is affected','Include environmental conditions if known'].map((tip,i) => <Text key={i} style={{ color: theme.textSecondary, fontSize:13, marginBottom:4 }}>- {tip}</Text>)}
        </View>
        <TouchableOpacity style={[s.btn, { backgroundColor: theme.primary }]} onPress={handleAnalyze} disabled={analyzing}>
          <View style={{ flexDirection:'row', alignItems:'center' }}>{analyzing ? <ActivityIndicator color="#fff" style={{ marginRight:8 }} /> : <Ionicons name="search" size={22} color="#fff" />}<Text style={{ color:'#fff', fontWeight:'700', marginLeft:8, fontSize:16 }}>{analyzing ? 'Analyzing...' : 'Analyze Symptoms'}</Text></View>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  c:{flex:1}, title:{fontSize:24,fontWeight:'700'}, label:{fontSize:15,fontWeight:'700',marginBottom:10},
  chip:{paddingHorizontal:16,paddingVertical:8,borderRadius:20,borderWidth:1,marginRight:8},
  textArea:{borderWidth:1,borderRadius:14,padding:16,fontSize:15,minHeight:140,lineHeight:22},
  tips:{marginTop:16,padding:16,borderRadius:12,borderWidth:1},
  btn:{height:54,borderRadius:14,alignItems:'center',justifyContent:'center',marginTop:20,marginBottom:32},
});
