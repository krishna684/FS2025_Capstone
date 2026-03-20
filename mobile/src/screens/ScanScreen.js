import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert, ActivityIndicator, ScrollView, Animated, Easing, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../services/api';

const { width: SW } = Dimensions.get('window');

function ScanOverlay({ analyzing, theme }) {
  const scanLine = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(1)).current;
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;
  const dot4 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!analyzing) return;
    // Scanning line animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(scanLine, { toValue: 1, duration: 1800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(scanLine, { toValue: 0, duration: 1800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
    // Pulse animation for corners
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1.15, duration: 800, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1, duration: 800, useNativeDriver: true }),
      ])
    ).start();
    // Scan point dots appearing sequentially
    const dotAnim = (dot, delay) => Animated.sequence([
      Animated.delay(delay),
      Animated.timing(dot, { toValue: 1, duration: 300, useNativeDriver: true }),
    ]);
    Animated.stagger(400, [dotAnim(dot1, 600), dotAnim(dot2, 200), dotAnim(dot3, 200), dotAnim(dot4, 200)]).start();
  }, [analyzing]);

  if (!analyzing) return null;

  const lineTranslate = scanLine.interpolate({ inputRange: [0, 1], outputRange: [0, 260] });

  return (
    <View style={StyleSheet.absoluteFill}>
      {/* Dark overlay */}
      <View style={[StyleSheet.absoluteFill, { backgroundColor: 'rgba(0,0,0,0.4)' }]} />

      {/* Scan frame */}
      <View style={{ position:'absolute', top:'15%', left:'10%', width:'80%', height:260 }}>
        {/* Corner brackets */}
        <Animated.View style={{ transform: [{ scale: pulse }] }}>
          <View style={{ position:'absolute', top:0, left:0, width:30, height:30, borderTopWidth:3, borderLeftWidth:3, borderColor: theme.primary, borderTopLeftRadius: 8 }} />
          <View style={{ position:'absolute', top:0, right:0, width:30, height:30, borderTopWidth:3, borderRightWidth:3, borderColor: theme.primary, borderTopRightRadius: 8 }} />
          <View style={{ position:'absolute', bottom:0, left:0, width:30, height:30, borderBottomWidth:3, borderLeftWidth:3, borderColor: theme.primary, borderBottomLeftRadius: 8 }} />
          <View style={{ position:'absolute', bottom:0, right:0, width:30, height:30, borderBottomWidth:3, borderRightWidth:3, borderColor: theme.primary, borderBottomRightRadius: 8 }} />
        </Animated.View>

        {/* Scanning line */}
        <Animated.View style={{ position:'absolute', left:8, right:8, height:2, backgroundColor: theme.primary, shadowColor: theme.primary, shadowOffset:{width:0,height:0}, shadowOpacity:0.8, shadowRadius:8, transform: [{ translateY: lineTranslate }] }} />

        {/* Scan point dots */}
        {[[dot1, '25%', '30%'], [dot2, '60%', '50%'], [dot3, '35%', '70%'], [dot4, '70%', '25%']].map(([dot, l, t], i) => (
          <Animated.View key={i} style={{ position:'absolute', left:l, top:t, opacity: dot, transform: [{ scale: dot }] }}>
            <View style={{ width:12, height:12, borderRadius:6, borderWidth:2, borderColor: theme.primary, backgroundColor: theme.primary+'40' }}>
              <View style={{ position:'absolute', top:-6, left:-6, width:24, height:24, borderRadius:12, borderWidth:1, borderColor: theme.primary+'50' }} />
            </View>
          </Animated.View>
        ))}
      </View>

      {/* Status text */}
      <View style={{ position:'absolute', bottom:'25%', alignSelf:'center', alignItems:'center' }}>
        <View style={{ flexDirection:'row', alignItems:'center', backgroundColor:'rgba(0,0,0,0.7)', paddingHorizontal:20, paddingVertical:12, borderRadius:24 }}>
          <ActivityIndicator color={theme.primary} size="small" />
          <Text style={{ color:'#fff', fontSize:15, fontWeight:'700', marginLeft:10 }}>AI Analyzing...</Text>
        </View>
        <Text style={{ color:'rgba(255,255,255,0.7)', fontSize:12, marginTop:8 }}>Detecting pests & diseases</Text>
      </View>
    </View>
  );
}

export default function ScanScreen({ navigation }) {
  const { theme } = useTheme(); const { t } = useLanguage();
  const [permission, requestPermission] = useCameraPermissions();
  const [showCamera, setShowCamera] = useState(false);
  const [image, setImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const cameraRef = useRef(null);

  async function takePhoto() {
    if (!permission?.granted) { const r = await requestPermission(); if (!r.granted) { Alert.alert('Permission needed', 'Camera access is required'); return; } }
    setShowCamera(true);
  }
  async function capturePhoto() {
    if (cameraRef.current) {
      const p = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      setImage(p.uri); setShowCamera(false);
    }
  }
  async function pickImage() {
    const r = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.8 });
    if (!r.canceled) { setImage(r.assets[0].uri); setError(null); }
  }
  async function analyzeImage() {
    if (!image) return;
    setAnalyzing(true); setError(null);
    try {
      // Run API call and 3-second minimum delay in parallel
      const [r] = await Promise.all([
        api.analyzeImage(image),
        new Promise(resolve => setTimeout(resolve, 3000)),
      ]);
      navigation.navigate('Results', { result: r, type: 'image', imageUri: image });
    } catch (e) {
      setError(e.message || 'Analysis failed. Check your connection and try again.');
    } finally { setAnalyzing(false); }
  }

  if (showCamera) return (
    <View style={{ flex: 1 }}>
      <CameraView ref={cameraRef} style={{ flex: 1 }} facing="back">
        <View style={{ flex:1, alignItems:'center', justifyContent:'center' }}><View style={{ width:260, height:260, borderWidth:3, borderColor:'rgba(255,255,255,0.7)', borderRadius:20 }} /><Text style={{ color:'#fff', fontSize:14, marginTop:16 }}>Position the leaf within the frame</Text></View>
        <View style={{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', paddingHorizontal:40, paddingBottom:50 }}>
          <TouchableOpacity style={{ width:50, height:50, borderRadius:25, backgroundColor:'rgba(0,0,0,0.5)', alignItems:'center', justifyContent:'center' }} onPress={() => setShowCamera(false)}><Ionicons name="close" size={28} color="#fff" /></TouchableOpacity>
          <TouchableOpacity style={{ width:72, height:72, borderRadius:36, borderWidth:4, borderColor:'#fff', alignItems:'center', justifyContent:'center' }} onPress={capturePhoto}><View style={{ width:58, height:58, borderRadius:29, backgroundColor:'#fff' }} /></TouchableOpacity>
          <View style={{ width:50 }} />
        </View>
      </CameraView>
    </View>
  );

  return (
    <View style={[{ flex: 1 }, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <Text style={[st.title, { color: theme.text }]}>{t('scan.title')}</Text>
        <Text style={{ color: theme.textSecondary, fontSize: 14, marginTop: 4, marginBottom: 20 }}>Upload or capture an image to detect pests</Text>

        {image ? (
          <View style={{ borderRadius:16, overflow:'hidden', position:'relative' }}>
            <Image source={{ uri: image }} style={{ width:'100%', height:300, borderRadius:16 }} />
            {!analyzing && <TouchableOpacity style={{ position:'absolute', top:10, right:10, backgroundColor:'rgba(0,0,0,0.5)', borderRadius:16, padding:4 }} onPress={() => { setImage(null); setError(null); }}><Ionicons name="close-circle" size={30} color="#fff" /></TouchableOpacity>}
            <ScanOverlay analyzing={analyzing} theme={theme} />
          </View>
        ) : (
          <TouchableOpacity style={[st.upload, { borderColor: theme.primary, backgroundColor: theme.card }]} onPress={pickImage}>
            <View style={{ width:72, height:72, borderRadius:36, backgroundColor:theme.primary+'15', alignItems:'center', justifyContent:'center', marginBottom:12 }}>
              <Ionicons name="cloud-upload-outline" size={36} color={theme.primary} />
            </View>
            <Text style={{ color: theme.text, fontSize:16, fontWeight:'600' }}>Tap to upload image</Text>
            <Text style={{ color: theme.textSecondary, fontSize:13, marginTop:4 }}>JPG, PNG, WebP supported</Text>
          </TouchableOpacity>
        )}

        {error && (
          <View style={{ backgroundColor: theme.danger+'15', borderRadius:12, padding:14, marginTop:16, flexDirection:'row', alignItems:'center' }}>
            <Ionicons name="alert-circle" size={20} color={theme.danger} />
            <Text style={{ color: theme.danger, fontSize:13, marginLeft:8, flex:1 }}>{error}</Text>
          </View>
        )}

        <View style={{ flexDirection:'row', marginTop:20 }}>
          <TouchableOpacity style={[st.actBtn, { backgroundColor: theme.primary }]} onPress={takePhoto}>
            <Ionicons name="camera" size={22} color="#fff" /><Text style={st.actBtnText}>{t('scan.camera')}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[st.actBtn, { backgroundColor: theme.info }]} onPress={pickImage}>
            <Ionicons name="image" size={22} color="#fff" /><Text style={st.actBtnText}>{t('scan.upload')}</Text>
          </TouchableOpacity>
        </View>

        {image && !analyzing && (
          <TouchableOpacity style={[st.analyzeBtn, { backgroundColor: theme.primary }]} onPress={analyzeImage}>
            <View style={{ flexDirection:'row', alignItems:'center' }}>
              <Ionicons name="scan" size={22} color="#fff" />
              <Text style={{ color:'#fff', fontWeight:'700', marginLeft:10, fontSize:16 }}>Analyze Image</Text>
            </View>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={[st.descBtn, { borderColor: theme.primary }]} onPress={() => navigation.navigate('Describe')}>
          <Ionicons name="create-outline" size={22} color={theme.primary} />
          <Text style={{ color: theme.primary, fontWeight:'700', marginLeft:8, fontSize:15 }}>Describe Symptoms Instead</Text>
        </TouchableOpacity>

        {/* Tips */}
        <View style={[st.tipsCard, { backgroundColor: theme.card, borderColor: theme.border }]}>
          <Text style={{ color: theme.text, fontWeight:'700', fontSize:15, marginBottom:10 }}>
            <Ionicons name="bulb-outline" size={16} color={theme.warning} /> Photo Tips
          </Text>
          {['Use natural lighting for best results', 'Get close to the affected area', 'Keep camera steady for sharp focus', 'Include both healthy and damaged parts'].map((tip, i) => (
            <View key={i} style={{ flexDirection:'row', alignItems:'center', marginBottom:6 }}>
              <View style={{ width:6, height:6, borderRadius:3, backgroundColor: theme.primary, marginRight:10 }} />
              <Text style={{ color: theme.textSecondary, fontSize:13 }}>{tip}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const st = StyleSheet.create({
  title:{fontSize:24,fontWeight:'700'},
  upload:{height:220,borderWidth:2,borderStyle:'dashed',borderRadius:16,alignItems:'center',justifyContent:'center'},
  actBtn:{flex:1,flexDirection:'row',alignItems:'center',justifyContent:'center',height:50,borderRadius:12,marginHorizontal:4},
  actBtnText:{color:'#fff',fontWeight:'700',marginLeft:8,fontSize:15},
  analyzeBtn:{height:54,borderRadius:14,alignItems:'center',justifyContent:'center',marginTop:20},
  descBtn:{flexDirection:'row',alignItems:'center',justifyContent:'center',height:50,borderRadius:12,borderWidth:2,marginTop:16},
  tipsCard:{borderRadius:14,padding:16,borderWidth:1,marginTop:20,marginBottom:20},
});
