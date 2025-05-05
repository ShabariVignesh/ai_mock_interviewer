import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayIcon, ClockIcon, TrendingUpIcon, ChevronRightIcon, DatabaseIcon, BarChart2Icon, NetworkIcon, LineChartIcon, BrainIcon, ServerIcon, TableIcon, GitBranchIcon } from 'lucide-react';
import { AnimatedTitle } from '../components/AnimatedTitle';
export function Home() {
  const navigate = useNavigate();
  const recentInterviews = [{
    company: 'Amazon',
    position: 'Senior Data Engineer',
    date: '2023-12-01',
    score: 88
  }, {
    company: 'Microsoft',
    position: 'Data Scientist',
    date: '2023-11-28',
    score: 92
  }];
  const stats = [{
    label: 'Data Questions',
    value: '2,000+',
    icon: DatabaseIcon
  }, {
    label: 'Success Rate',
    value: '92%',
    icon: TrendingUpIcon
  }, {
    label: 'Data Domains',
    value: '8+',
    icon: NetworkIcon
  }, {
    label: 'Interview Types',
    value: '12+',
    icon: GitBranchIcon
  }];
  const features = [{
    title: 'Data-Specific Questions',
    description: 'Specialized questions covering SQL, Python, Big Data, and Machine Learning',
    icon: TableIcon,
    gradient: 'from-sjsu-blue via-blue-500 to-cyan-500'
  }, {
    title: 'Real-time Analysis',
    description: 'Advanced analytics of your responses with technical accuracy assessment',
    icon: LineChartIcon,
    gradient: 'from-blue-600 via-purple-500 to-sjsu-blue'
  }, {
    title: 'Domain Expertise',
    description: 'Questions tailored to data engineering, science, and analytics roles',
    icon: BrainIcon,
    gradient: 'from-sjsu-blue via-teal-500 to-blue-500'
  }];
  return <div className="relative">
      <div className="absolute top-0 right-0 w-1/3 h-1/3 bg-gradient-to-br from-sjsu-gold/20 via-sjsu-blue/10 to-transparent rounded-full blur-3xl -z-10 animate-pulse-slow" />
      <div className="absolute bottom-0 left-0 w-1/3 h-1/3 bg-gradient-to-tr from-sjsu-blue/20 via-blue-500/10 to-transparent rounded-full blur-3xl -z-10 animate-pulse-slow" />
      <section className="relative pt-20 pb-16 overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <div className="flex items-center space-x-3 mb-6">
                  <img src="/San_Jose_State_Spartans_logo.png" alt="SJSU Logo" className="h-16 w-auto animate-float" />
                  <div className="px-4 py-2 bg-gradient-to-r from-sjsu-blue/10 to-blue-500/10 backdrop-blur-sm border border-sjsu-blue/20 text-sjsu-blue rounded-xl text-sm font-medium">
                    Data Interview Preparation
                  </div>
                </div>
                <AnimatedTitle />
                <p className="text-xl text-gray-600 leading-relaxed">
                  Master your data interviews with our AI-powered platform.
                  Specialized in data engineering, science, and analytics
                  positions.
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <button onClick={() => navigate('/setup')} className="group px-8 py-4 bg-gradient-to-r from-sjsu-blue to-blue-600 text-white rounded-xl font-medium flex items-center space-x-2 hover:shadow-lg hover:shadow-blue-500/20 transform hover:-translate-y-0.5 transition-all">
                  <PlayIcon className="w-5 h-5" />
                  <span>Start Interview</span>
                  <ChevronRightIcon className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
                <a href="#features" className="text-sjsu-blue hover:text-blue-700 font-medium flex items-center space-x-1 group">
                  <span>Explore Features</span>
                  <ChevronRightIcon className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </a>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div className="bg-gradient-to-br from-sjsu-blue/5 to-transparent backdrop-blur-sm border border-sjsu-blue/10 rounded-lg p-4">
                  <div className="text-2xl font-bold text-sjsu-blue">95%</div>
                  <div className="text-sm text-gray-600">
                    Interview Success Rate
                  </div>
                </div>
                <div className="bg-gradient-to-br from-sjsu-gold/5 to-transparent backdrop-blur-sm border border-sjsu-gold/10 rounded-lg p-4">
                  <div className="text-2xl font-bold text-sjsu-gold">2000+</div>
                  <div className="text-sm text-gray-600">Data Questions</div>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="relative bg-gradient-to-b from-sjsu-blue/5 to-transparent p-8 rounded-2xl">
                <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-xl p-6 space-y-6 border border-white/20">
                  {recentInterviews.map((interview, index) => <div key={index} className="group bg-white rounded-lg p-4 border border-gray-100 hover:shadow-md transition-all relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-r from-sjsu-blue/5 via-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                      <div className="flex items-start justify-between relative">
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {interview.position}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {interview.company}
                          </p>
                          <div className="flex items-center mt-2 text-sm text-gray-500">
                            <ClockIcon className="w-4 h-4 mr-1" />
                            {interview.date}
                          </div>
                        </div>
                        <div className="flex flex-col items-end space-y-2">
                          <div className="flex items-center px-3 py-1 bg-green-50 text-green-600 rounded-full">
                            <BarChart2Icon className="w-4 h-4 mr-1" />
                            <span className="font-medium">
                              {interview.score}%
                            </span>
                          </div>
                          <button onClick={() => navigate('/setup')} className="text-sm text-sjsu-blue hover:text-blue-600 group-hover:underline">
                            View Details
                          </button>
                        </div>
                      </div>
                    </div>)}
                </div>
              </div>
              <div className="absolute -top-4 -right-4 w-24 h-24 bg-gradient-to-br from-sjsu-gold/20 to-transparent rounded-full blur-2xl" />
              <div className="absolute -bottom-4 -left-4 w-24 h-24 bg-gradient-to-tr from-sjsu-blue/20 to-transparent rounded-full blur-2xl" />
            </div>
          </div>
        </div>
      </section>
      <section className="py-16 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-white via-gray-50 to-white" />
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
            const Icon = stat.icon;
            return <div key={index} className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-all border border-gray-100 hover:border-sjsu-blue/20">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-gradient-to-br from-sjsu-blue/10 to-transparent text-sjsu-blue rounded-lg group-hover:scale-110 transition-transform">
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-gray-900">
                        {stat.value}
                      </div>
                      <div className="text-sm text-gray-500">{stat.label}</div>
                    </div>
                  </div>
                </div>;
          })}
          </div>
        </div>
      </section>
      <section id="features" className="py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sjsu-blue to-blue-600">
              Specialized in Data Interviews
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Advanced features designed specifically for data professionals
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => {
            const Icon = feature.icon;
            return <div key={index} className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-xl transition-all border border-gray-100 relative overflow-hidden">
                  <div className={`absolute inset-0 bg-gradient-to-r ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity`} />
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-br from-sjsu-blue/10 to-transparent rounded-lg flex items-center justify-center text-sjsu-blue mb-4 group-hover:scale-110 transition-transform">
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </div>
                </div>;
          })}
          </div>
        </div>
      </section>
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-sjsu-blue to-blue-600 rounded-2xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-radial from-white/10 to-transparent" />
            <div className="relative z-10">
              <div className="max-w-2xl">
                <h2 className="text-3xl font-bold text-white mb-4">
                  Ready to Excel in Your Data Interview?
                </h2>
                <p className="text-blue-100 mb-8">
                  Practice with our specialized AI system and master technical
                  interviews for data roles
                </p>
                <button onClick={() => navigate('/setup')} className="group px-8 py-4 bg-white text-sjsu-blue rounded-xl font-medium hover:bg-blue-50 transition-all inline-flex items-center space-x-2">
                  <ServerIcon className="w-5 h-5" />
                  <span>Start Practicing Now</span>
                  <ChevronRightIcon className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-white/5 to-transparent rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-white/5 to-transparent rounded-full blur-3xl" />
          </div>
        </div>
      </section>
    </div>;
}