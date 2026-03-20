import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';

const TEAM = [{ name:'Dhanya Boyapally', role:'Computer Vision & ML Researcher', icon:'eye', color:'#8b5cf6' },{ name:'Krishna Karra', role:'Backend & Frontend Developer', icon:'code-slash', color:'#3b82f6' },{ name:'Jack Frater', role:'Frontend & UI/UX Designer', icon:'color-palette', color:'#f59e0b' },{ name:'Biao Wang', role:'Machine Learning & AI Specialist', icon:'hardware-chip', color:'#10b981' }];

export default function AboutScreen() {
  const { theme } = useTheme();
  return (
    <ScrollView style={[s.c, { backgroundColor:theme.background }]} contentContainerStyle={{ paddingBottom:20 }}>
      <View style={[s.hero, { backgroundColor:theme.primary+'10' }]}><View style={[s.logo, { backgroundColor:theme.primary+'20' }]}><Ionicons name="leaf" size={40} color={theme.primary} /></View><Text style={[s.brand, { color:theme.primary }]}>AGBOT</Text><Text style={{ color:theme.textSecondary, fontSize:13, marginTop:4, textAlign:'center' }}>From Data to Harvest - Smarter Solutions for Farmers</Text></View>
      <View style={[s.card, { backgroundColor:theme.card, borderColor:theme.border }]}><Text style={[s.sec, { color:theme.text }]}>Our Mission</Text><Text style={{ color:theme.textSecondary, fontSize:14, lineHeight:22 }}>AGBOT aims to reduce pesticide use by 40% through precise AI-powered pest detection, protecting beneficial insects and soil health while reducing crop losses and promoting food security for farmers worldwide.</Text></View>
      <View style={s.impactRow}>{[{ l:'Pesticide Reduction',v:'40%',icon:'trending-down',c:theme.success },{ l:'AI Accuracy',v:'94%',icon:'analytics',c:theme.info },{ l:'Crop Types',v:'20+',icon:'leaf',c:theme.primary }].map((it,i) => <View key={i} style={[s.impactCard, { backgroundColor:theme.card, borderColor:theme.border }]}><Ionicons name={it.icon} size={24} color={it.c} /><Text style={{ color:it.c, fontSize:22, fontWeight:'800', marginTop:6 }}>{it.v}</Text><Text style={{ color:theme.textSecondary, fontSize:10, marginTop:2, textAlign:'center' }}>{it.l}</Text></View>)}</View>
      <Text style={[s.sec, { color:theme.text, marginHorizontal:16 }]}>Our Team</Text>
      {TEAM.map((m,i) => <View key={i} style={[s.teamCard, { backgroundColor:theme.card, borderColor:theme.border }]}><View style={[s.teamIcon, { backgroundColor:m.color+'20' }]}><Ionicons name={m.icon} size={24} color={m.color} /></View><View><Text style={{ color:theme.text, fontSize:15, fontWeight:'700' }}>{m.name}</Text><Text style={{ color:theme.textSecondary, fontSize:12, marginTop:2 }}>{m.role}</Text></View></View>)}
      <View style={[s.card, { backgroundColor:theme.card, borderColor:theme.border, marginBottom:40 }]}><Text style={{ color:theme.textSecondary, fontSize:12, fontWeight:'600', textTransform:'uppercase', letterSpacing:1 }}>Mentor</Text><Text style={{ color:theme.text, fontSize:17, fontWeight:'700', marginTop:4 }}>Professor Noel Aloysius</Text><Text style={{ color:theme.textSecondary, fontSize:13, marginTop:2 }}>University of Missouri</Text></View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  c:{flex:1}, hero:{alignItems:'center',padding:32,borderBottomLeftRadius:24,borderBottomRightRadius:24}, logo:{width:80,height:80,borderRadius:40,alignItems:'center',justifyContent:'center',marginBottom:12}, brand:{fontSize:28,fontWeight:'800',letterSpacing:2},
  card:{margin:16,borderRadius:14,padding:16,borderWidth:1}, sec:{fontSize:18,fontWeight:'700',marginBottom:10},
  impactRow:{flexDirection:'row',paddingHorizontal:12}, impactCard:{flex:1,padding:14,borderRadius:14,borderWidth:1,alignItems:'center',marginHorizontal:4},
  teamCard:{flexDirection:'row',alignItems:'center',marginHorizontal:16,marginBottom:8,padding:14,borderRadius:12,borderWidth:1}, teamIcon:{width:44,height:44,borderRadius:12,alignItems:'center',justifyContent:'center',marginRight:14},
});
