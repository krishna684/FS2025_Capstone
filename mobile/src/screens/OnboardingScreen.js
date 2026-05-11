import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions, Animated, FlatList } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: W, height: H } = Dimensions.get('window');

const SLIDES = [
  {
    icon: 'leaf',
    iconBg: '#10b981',
    title: 'Welcome to AGBOT',
    subtitle: 'From Data to Harvest',
    description: 'AI-powered plant pest detection that helps you protect your crops and increase yield.',
    features: ['Instant pest identification', '18 pest & disease classes', '88% AI accuracy'],
  },
  {
    icon: 'camera',
    iconBg: '#3b82f6',
    title: 'Scan Your Plants',
    subtitle: 'Quick & Easy',
    description: 'Take a photo of any affected plant leaf and get instant AI analysis with treatment recommendations.',
    features: ['Camera or gallery upload', '3-second AI analysis', 'Detailed scan results'],
  },
  {
    icon: 'chatbubbles',
    iconBg: '#8b5cf6',
    title: 'Ask the Expert',
    subtitle: 'Chat with AGBOT',
    description: 'Get answers about pest symptoms, remedies, and prevention. Like having an agricultural expert in your pocket.',
    features: ['15 pest species covered', 'Treatment advice', 'Prevention tips'],
  },
  {
    icon: 'analytics',
    iconBg: '#f59e0b',
    title: 'Track & Improve',
    subtitle: 'Smart Dashboard',
    description: 'Monitor your scan history, track pest trends, and export reports to make data-driven farming decisions.',
    features: ['Scan history with images', 'PDF reports & sharing', 'Severity analytics'],
  },
];

function Slide({ item, index }) {
  return (
    <View style={[s.slide, { width: W }]}>
      {/* Icon */}
      <View style={[s.iconCircle, { backgroundColor: item.iconBg + '15' }]}>
        <View style={[s.iconInner, { backgroundColor: item.iconBg + '25' }]}>
          <Ionicons name={item.icon} size={52} color={item.iconBg} />
        </View>
      </View>

      {/* Text */}
      <Text style={s.title}>{item.title}</Text>
      <Text style={[s.subtitle, { color: item.iconBg }]}>{item.subtitle}</Text>
      <Text style={s.description}>{item.description}</Text>

      {/* Features */}
      <View style={s.features}>
        {item.features.map((f, i) => (
          <View key={i} style={s.featureRow}>
            <View style={[s.featureDot, { backgroundColor: item.iconBg }]}>
              <Ionicons name="checkmark" size={12} color="#fff" />
            </View>
            <Text style={s.featureText}>{f}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

export default function OnboardingScreen({ onComplete }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef(null);
  const scrollX = useRef(new Animated.Value(0)).current;

  function goNext() {
    if (currentIndex < SLIDES.length - 1) {
      flatListRef.current?.scrollToIndex({ index: currentIndex + 1, animated: true });
      setCurrentIndex(currentIndex + 1);
    } else {
      completeOnboarding();
    }
  }

  function skip() {
    completeOnboarding();
  }

  async function completeOnboarding() {
    await AsyncStorage.setItem('onboarding_complete', 'true');
    onComplete();
  }

  const onViewableItemsChanged = useRef(({ viewableItems }) => {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index);
    }
  }).current;

  const isLast = currentIndex === SLIDES.length - 1;

  return (
    <View style={s.container}>
      {/* Skip button */}
      {!isLast && (
        <TouchableOpacity style={s.skipBtn} onPress={skip}>
          <Text style={s.skipText}>Skip</Text>
        </TouchableOpacity>
      )}

      {/* Slides */}
      <FlatList
        ref={flatListRef}
        data={SLIDES}
        renderItem={({ item, index }) => <Slide item={item} index={index} />}
        keyExtractor={(_, i) => i.toString()}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        bounces={false}
        onScroll={Animated.event([{ nativeEvent: { contentOffset: { x: scrollX } } }], { useNativeDriver: false })}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={{ viewAreaCoveragePercentThreshold: 50 }}
      />

      {/* Bottom section */}
      <View style={s.bottom}>
        {/* Dots */}
        <View style={s.dots}>
          {SLIDES.map((slide, i) => {
            const inputRange = [(i - 1) * W, i * W, (i + 1) * W];
            const dotWidth = scrollX.interpolate({ inputRange, outputRange: [8, 28, 8], extrapolate: 'clamp' });
            const dotOpacity = scrollX.interpolate({ inputRange, outputRange: [0.3, 1, 0.3], extrapolate: 'clamp' });
            return (
              <Animated.View key={i} style={[s.dot, {
                width: dotWidth,
                opacity: dotOpacity,
                backgroundColor: slide.iconBg,
              }]} />
            );
          })}
        </View>

        {/* Button */}
        <TouchableOpacity style={[s.nextBtn, { backgroundColor: SLIDES[currentIndex].iconBg }]} onPress={goNext} activeOpacity={0.8}>
          {isLast ? (
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={s.nextBtnText}>Get Started</Text>
              <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 8 }} />
            </View>
          ) : (
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={s.nextBtnText}>Next</Text>
              <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 8 }} />
            </View>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  skipBtn: { position: 'absolute', top: 60, right: 24, zIndex: 10, padding: 8 },
  skipText: { color: '#6b7280', fontSize: 16, fontWeight: '600' },
  slide: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 36, paddingBottom: 120 },
  iconCircle: { width: 140, height: 140, borderRadius: 70, alignItems: 'center', justifyContent: 'center', marginBottom: 32 },
  iconInner: { width: 100, height: 100, borderRadius: 50, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 28, fontWeight: '800', color: '#111827', textAlign: 'center', marginBottom: 4 },
  subtitle: { fontSize: 16, fontWeight: '700', textAlign: 'center', marginBottom: 16 },
  description: { fontSize: 15, color: '#6b7280', textAlign: 'center', lineHeight: 22, marginBottom: 28 },
  features: { alignSelf: 'stretch' },
  featureRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, paddingHorizontal: 8 },
  featureDot: { width: 22, height: 22, borderRadius: 11, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  featureText: { fontSize: 14, color: '#374151', fontWeight: '500' },
  bottom: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingBottom: 50, paddingHorizontal: 24, alignItems: 'center' },
  dots: { flexDirection: 'row', alignItems: 'center', marginBottom: 24 },
  dot: { height: 8, borderRadius: 4, marginHorizontal: 4 },
  nextBtn: { width: '100%', height: 56, borderRadius: 16, alignItems: 'center', justifyContent: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 8, elevation: 4 },
  nextBtnText: { color: '#fff', fontSize: 17, fontWeight: '700' },
});
