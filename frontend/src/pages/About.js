import { Mountain } from 'lucide-react';
import { Link } from 'react-router-dom';

const team = [
  {
    id: 1,
    name: 'Stanzin Dorje',
    role: 'Founder & Lead Rider',
    bio: 'Born and raised in Leh, Stanzin has ridden every road in Ladakh over 200 times. He founded Ladakh Moto to help travellers experience the region safely and authentically.',
    img: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=400&auto=format&fit=crop',
  },
  {
    id: 2,
    name: 'Rigzin Namgyal',
    role: 'Head of Operations',
    bio: 'Rigzin oversees shop partnerships and bike quality checks. With 10 years in the tourism industry, he ensures every rental meets our high safety standards.',
    img: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=400&auto=format&fit=crop',
  },
  {
    id: 3,
    name: 'Padma Angmo',
    role: 'Customer Experience',
    bio: 'Padma is your first point of contact for any support. She speaks Ladakhi, Hindi, and English, and is passionate about making every rider feel at home in Ladakh.',
    img: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=400&auto=format&fit=crop',
  },
  {
    id: 4,
    name: 'Tashi Wangchuk',
    role: 'Route Expert',
    bio: 'Tashi has mapped over 50 routes across Ladakh and the Himalayas. He curates our recommended rides and advises riders on altitude, weather, and road conditions.',
    img: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=400&auto=format&fit=crop',
  },
  {
    id: 5,
    name: 'Dechen Lamo',
    role: 'Marketing & Partnerships',
    bio: 'Dechen connects Ladakh Moto with travel agents, hotels, and adventure bloggers worldwide. She has grown our community to over 2,500 happy riders.',
    img: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=400&auto=format&fit=crop',
  },
  {
    id: 6,
    name: 'Sonam Phuntsog',
    role: 'Lead Mechanic',
    bio: 'Sonam is the person who keeps every bike in top shape. He trains all partner shops on maintenance and conducts surprise quality checks throughout the season.',
    img: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=400&auto=format&fit=crop',
  },
];

export default function About() {
  return (
    <div className="min-h-screen bg-background" data-testid="about-page">

      {/* Hero */}
      <section className="relative h-64 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1768410318326-0b8a4db813f1?q=80&w=2400&auto=format&fit=crop"
          alt="Ladakh landscape"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/55" />
        <div className="relative z-10 h-full flex flex-col items-center justify-center text-center text-white px-6">
          <h1 className="font-heading font-extrabold text-4xl sm:text-5xl">Meet the Team</h1>
          <p className="mt-3 text-white/80 text-base max-w-xl">
            The people behind Ladakh Moto — riders, locals, and adventure lovers.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="py-14 px-6 md:px-12 max-w-3xl mx-auto text-center">
        <h2 className="font-heading font-bold text-2xl text-foreground mb-4">Our Mission</h2>
        <p className="text-muted-foreground text-base leading-relaxed">
          We believe the roads of Ladakh are among the most breathtaking on earth — and everyone deserves to ride them safely.
          Ladakh Moto connects travellers with trusted local bike shops, so you spend less time worrying and more time riding.
        </p>
      </section>

      {/* Team Grid */}
      <section className="py-10 pb-24 px-6 md:px-12 lg:px-24">
        <div className="max-w-6xl mx-auto">
          <h2 className="font-heading font-bold text-2xl text-foreground text-center mb-10">The People Behind the Ride</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {team.map(member => (
              <div key={member.id} className="bg-secondary/40 rounded-2xl overflow-hidden hover:shadow-lg transition-shadow duration-300">
                <div className="aspect-[4/3] overflow-hidden">
                  <img
                    src={member.img}
                    alt={member.name}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="p-5">
                  <h3 className="font-heading font-bold text-lg text-foreground">{member.name}</h3>
                  <p className="text-primary text-sm font-semibold mt-0.5">{member.role}</p>
                  <p className="text-muted-foreground text-sm leading-relaxed mt-3">{member.bio}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-10 px-6 md:px-12 lg:px-24">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Mountain className="w-5 h-5 text-primary" strokeWidth={2} />
            <span className="font-heading font-bold text-base">Ladakh Moto</span>
          </div>
          <p className="text-xs text-muted-foreground font-body">
            Leh, Ladakh, India · Built for adventure
          </p>
        </div>
      </footer>

    </div>
  );
}