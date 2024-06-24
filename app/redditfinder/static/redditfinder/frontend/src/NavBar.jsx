import React from 'react';
import { Icon } from '@iconify/react';
import homeIcon from '@iconify-icons/fa/home';
import infoCircle from '@iconify-icons/fa/info-circle';
import envelope from '@iconify-icons/fa/envelope';
import user from '@iconify-icons/fa/user';

const NavBar = () => {
    return (
        <div className="bg-primary-dark fixed top-0 left-0 w-full h-16 m-0 flex flex-row items-center justify-around shadow-lg">
            <NavBarIcon icon={homeIcon} />
            <NavBarIcon icon={infoCircle} />
            <NavBarIcon icon={envelope} />
            <NavBarIcon icon={user} />
        </div>
    );
};

const NavBarIcon = ({ icon }) => (
    <div className="navbar-icon">
        <Icon icon={icon} width="24" height="24" />
    </div>
);

export default NavBar;
