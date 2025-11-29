'use client';

interface CountryFlagProps {
  countryCode?: string;
  countryName?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Map country names to ISO codes for flag emoji
const countryToCode: Record<string, string> = {
  'australia': 'AU',
  'austria': 'AT',
  'azerbaijan': 'AZ',
  'bahrain': 'BH',
  'belgium': 'BE',
  'brazil': 'BR',
  'canada': 'CA',
  'china': 'CN',
  'netherlands': 'NL',
  'france': 'FR',
  'germany': 'DE',
  'hungary': 'HU',
  'italy': 'IT',
  'japan': 'JP',
  'mexico': 'MX',
  'monaco': 'MC',
  'portugal': 'PT',
  'qatar': 'QA',
  'saudi arabia': 'SA',
  'singapore': 'SG',
  'spain': 'ES',
  'uae': 'AE',
  'united arab emirates': 'AE',
  'uk': 'GB',
  'united kingdom': 'GB',
  'great britain': 'GB',
  'usa': 'US',
  'united states': 'US',
  'miami': 'US',
  'las vegas': 'US',
  'austin': 'US',
};

const sizeClasses = {
  sm: 'w-6 h-4',
  md: 'w-8 h-6',
  lg: 'w-12 h-8',
  xl: 'w-16 h-12',
};

export function CountryFlag({
  countryCode,
  countryName,
  className = '',
  size = 'md'
}: CountryFlagProps) {
  // Determine the country code
  let code = countryCode;
  if (!code && countryName) {
    const normalized = countryName.toLowerCase().trim();
    code = countryToCode[normalized];
  }

  if (!code) {
    return null;
  }

  // Convert to flag emoji using regional indicator symbols
  const codePoints = code
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  const flagEmoji = String.fromCodePoint(...codePoints);

  return (
    <span
      className={`inline-flex items-center justify-center ${sizeClasses[size]} text-2xl ${className}`}
      title={countryName || code}
      role="img"
      aria-label={`${countryName || code} flag`}
    >
      {flagEmoji}
    </span>
  );
}
