interface PasswordStrengthProps {
  password: string;
  showRequirements?: boolean;
}

export function PasswordStrength({ password, showRequirements = true }: PasswordStrengthProps) {
  const requirements = [
    { regex: /.{8,}/, text: 'At least 8 characters' },
    { regex: /[A-Z]/, text: 'One uppercase letter' },
    { regex: /[a-z]/, text: 'One lowercase letter' },
    { regex: /[0-9]/, text: 'One number' },
    { regex: /[^A-Za-z0-9]/, text: 'One special character' },
  ];

  const strength = requirements.filter(req => req.regex.test(password)).length;
  
  const getStrengthColor = () => {
    if (strength === 0) return 'bg-gray-200';
    if (strength <= 2) return 'bg-red-500';
    if (strength <= 3) return 'bg-orange-500';
    if (strength <= 4) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStrengthText = () => {
    if (strength === 0) return '';
    if (strength <= 2) return 'Weak';
    if (strength <= 3) return 'Fair';
    if (strength <= 4) return 'Good';
    return 'Strong';
  };

  return (
    <div className="space-y-2">
      {password && (
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-600">Password strength</span>
            <span className={`text-sm font-medium ${
              strength <= 2 ? 'text-red-600' : 
              strength <= 3 ? 'text-orange-600' : 
              strength <= 4 ? 'text-yellow-600' : 
              'text-green-600'
            }`}>
              {getStrengthText()}
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${getStrengthColor()}`}
              style={{ width: `${(strength / 5) * 100}%` }}
            />
          </div>
        </div>
      )}
      
      {showRequirements && (
        <ul className="space-y-1 text-sm">
          {requirements.map((req, index) => (
            <li
              key={index}
              className={`flex items-center ${
                password && req.regex.test(password) ? 'text-green-600' : 'text-gray-500'
              }`}
            >
              <span className="mr-2">
                {password && req.regex.test(password) ? '✓' : '○'}
              </span>
              {req.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}